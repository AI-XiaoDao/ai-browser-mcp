
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

#ifdef _DEBUG
#define MCHECK_MEM_POINTER(p)  ASSERT ((BYTE*)(p) < GetPtr () || (BYTE*)(p) >= GetPtr () + GetSize ());
#else
    #define MCHECK_MEM_POINTER(p)
#endif

CVolMem::CVolMem ()
{
    m_pData = NULL;
    m_npAllocedSize = m_npSize = 0;
    m_npMemAlignSize = _DEFAULT_MEM_ALIGN_SIZE;
}

void CVolMem::_CopySelfFrom (const CVolMem& objCopyFrom)
{
    CopyFrom (objCopyFrom.GetPtr (), objCopyFrom.GetSize ());
}

BOOL CVolMem::_IsSelfEqual (const CVolMem& objCompare) const
{
    return (m_npSize == objCompare.m_npSize && memcmp (m_pData, objCompare.m_pData, m_npSize) == 0);
}

CVolMem::CVolMem (const CVolString& str) : CVolMem ()
{
    AddOnlyText (str.GetText ());
}

void CVolMem::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    if (nMaxDumpSize == 0)  // 使用默认尺寸?
        nMaxDumpSize = 1024;

    const BYTE* pb = GetPtr ();
    const INT_P npDataSize = GetSize ();
    const INT_P npDumpedDataSize = (nMaxDumpSize < 0 ? npDataSize : MIN (npDataSize, nMaxDumpSize));
    const BYTE* pbEnd = pb + npDumpedDataSize;

    if (npDataSize == npDumpedDataSize)
        strDump.AddFormatText (_T_BIN_BYTES_DUMPED1_D, (INT)npDataSize);
    else
        strDump.AddFormatText (_T_BIN_BYTES_DUMPED2_DDD, (INT)npDataSize, npDumpedDataSize, (INT)(npDataSize - npDumpedDataSize));

    TCHAR buf [64];
    for (INT_P npIndex = 0; pb < pbEnd; )
    {
        strDump.AddText (_T ("\r\n["));
        strDump.AddText (DWordToHexStr ((DWORD)npIndex, 8, buf, NUM_ELEMENTS_OF (buf)));
        strDump.AddText (_T ("]:"));

        CVolString strText;

        INT_P npIndex2 = 0;
        for (; pb < pbEnd && npIndex2 < 16; npIndex2++, npIndex++, pb++)
        {
            strDump.AddChar (' ');
            strDump.AddText (ByteToHexStr (*pb, 2, buf, NUM_ELEMENTS_OF (buf)));

            strText.AddChar (isprint ((INT)(DWORD)*pb) ? (TCHAR)*pb : '.');
        }

        strDump.AddChar (' ', (16 - npIndex2) * 3);
        strDump.AddText (_T (" | "));
        strDump.AddText (strText);
    }
}

BYTE* CVolMem::Alloc (const INT_P npSize)
{
    ASSERT (npSize >= 0);

    if (m_pData != NULL)
        return Realloc (npSize);

    if (npSize == 0)
        return NULL;

    // 计算对齐后的内存分配尺寸
    const INT_P npMemAlignSize = (m_npMemAlignSize <= 0 ? _DEFAULT_MEM_ALIGN_SIZE : m_npMemAlignSize);
    const INT_P npAllocSize = npSize + npMemAlignSize - (npSize % npMemAlignSize);
    ASSERT (npAllocSize >= npSize);

    m_pData = (BYTE*)mgrAlloc (npAllocSize);
    m_npAllocedSize = npAllocSize;
    m_npSize = npSize;

    return m_pData;
}

BYTE* CVolMem::Realloc (const INT_P npSize)
{
    ASSERT (npSize >= 0);

    if (npSize == m_npSize)
        return m_pData;

    if (npSize == 0)
    {
        Free ();
        return NULL;
    }

    if (m_pData == NULL)
        return Alloc (npSize);

    const INT_P npMemAlignSize = (m_npMemAlignSize <= 0 ? _DEFAULT_MEM_ALIGN_SIZE : m_npMemAlignSize);
    if (m_npAllocedSize >= npSize &&  // 满足所欲分配的尺寸?
            m_npAllocedSize - npSize <= npMemAlignSize)  // 富余空间尺寸未超出太多?
    {
        m_npSize = npSize;
        return m_pData;
    }

    //---------------------------------------------

    // 计算对齐后的内存分配尺寸
    const INT_P npAllocSize = npSize + npMemAlignSize - (npSize % npMemAlignSize);
    ASSERT (npAllocSize >= npSize);

    m_pData = (BYTE*)mgrRealloc (m_pData, npAllocSize);
    m_npAllocedSize = npAllocSize;
    m_npSize = npSize;

    return m_pData;
}

void CVolMem::Free ()
{
    if (m_pData != NULL)
        mgrFree (m_pData);

    m_pData = NULL;
    m_npAllocedSize = m_npSize = 0;
}

void* CVolMem::AddSpace (const INT_P npSize, const BOOL_P blpZero)
{
    ASSERT (npSize >= 0);

    const INT_P npOldSize = GetSize ();
    void* p = Realloc (npOldSize + npSize) + npOldSize;

    if (blpZero)
        ZERO_MEM (p, npSize);

    return p;
}

void* CVolMem::InsertSpace (const INT_P npOffset, const INT_P npSize, const BOOL_P blpZero)
{
    ASSERT (npOffset >= 0 && npSize >= 0);

    if (npOffset >= m_npSize)  // 在尾部插入?
    {
        return AddSpace (npSize, blpZero);
    }
    else  // 在中间插入
    {
        const INT_P npOldSize = m_npSize;

        BYTE* pInsertAt = Realloc (npOldSize + npSize) + npOffset;
        memmove (pInsertAt + npSize, pInsertAt, npOldSize - npOffset);

        if (blpZero)
            ZERO_MEM (pInsertAt, npSize);

        return pInsertAt;
    }
}

//---------------------------------------------------------

void CVolMem::AddManyChars (const TCHAR ch, const INT_P npCount)
{
    if (npCount <= 0)
        return;

    TCHAR* ps = (TCHAR*)AddSpace (npCount * sizeof (TCHAR), FALSE);
    for (INT_P np = 0; np < npCount; np++)
        *ps++ = ch;
    ASSERT (IsAtEnd (ps));
}

void CVolMem::AddManyWChars (const WCHAR ch, const INT_P npCount)
{
    if (npCount <= 0)
        return;

    WCHAR* ps = (WCHAR*)AddSpace (npCount * sizeof (WCHAR), FALSE);
    for (INT_P np = 0; np < npCount; np++)
        *ps++ = ch;
    ASSERT (IsAtEnd (ps));
}

void CVolMem::AddManyU8Chars (const U8CHAR ch, const INT_P npCount)
{
    if (npCount <= 0)
        return;

    U8CHAR* ps = (U8CHAR*)AddSpace (npCount * sizeof (U8CHAR), FALSE);
    for (INT_P np = 0; np < npCount; np++)
        *ps++ = ch;
    ASSERT (IsAtEnd (ps));
}

void CVolMem::AddManyCopies (const void* pData, const INT_P npDataSize, const INT_P npNumAddCopies)
{
#ifdef _DEBUG
    if (pData != NULL)
    {
        ASSERT_R_ADR (pData, npDataSize);
        ASSERT (npNumAddCopies >= 0);
    }
#endif

    if (npDataSize <= 0 || npNumAddCopies <= 0)
        return;

    // 分配对应尺寸的空间
    BYTE* pb = (BYTE*)AddSpace (npNumAddCopies * npDataSize, (pData == NULL));

    if (pData == NULL)
        return;

    // 填写数据
    switch (npDataSize)
    {
    case (INT_P)sizeof (BYTE):  {
        const BYTE bt = *(BYTE*)pData;
        for (INT_P npIndex = 0; npIndex < npNumAddCopies; npIndex++, pb++)
            *pb = bt;
        ASSERT (IsAtEnd (pb));
        break;  }

    case (INT_P)sizeof (WORD):  {
        const WORD w = *(WORD*)pData;
        WORD* pw = (WORD*)pb;
        for (INT_P npIndex = 0; npIndex < npNumAddCopies; npIndex++, pw++)
            *pw = w;
        ASSERT (IsAtEnd (pw));
        break;  }

    case (INT_P)sizeof (DWORD):  {
        const DWORD dw = *(DWORD*)pData;
        DWORD* pdw = (DWORD*)pb;
        for (INT_P npIndex = 0; npIndex < npNumAddCopies; npIndex++, pdw++)
            *pdw = dw;
        ASSERT (IsAtEnd (pdw));
        break;  }

    case (INT_P)sizeof (UINT64):  {
        const UINT64 u64 = *(UINT64*)pData;
        UINT64* pu64 = (UINT64*)pb;
        for (INT_P npIndex = 0; npIndex < npNumAddCopies; npIndex++, pu64++)
            *pu64 = u64;
        ASSERT (IsAtEnd (pu64));
        break;  }

    default:  {
        for (INT_P npIndex = 0; npIndex < npNumAddCopies; npIndex++, pb += npDataSize)
            COPY_MEM (pb, pData, npDataSize);
        ASSERT (IsAtEnd (pb));
        break;  }
    }
}

CVolMem& CVolMem::AddManyBytes (const INT_P npNumBytes, ...)
{
    ASSERT (npNumBytes > 0);

    va_list argList;
    va_start (argList, npNumBytes);

    const INT_P npOldSize = m_npSize;
    BYTE* pb = Realloc (m_npSize + npNumBytes) + npOldSize;
    for (INT_P np = 0; np < npNumBytes; np++)
        *pb++ = (BYTE)va_arg (argList, int);

    va_end (argList);
    return *this;
}

void CVolMem::AddString (const WCHAR* pws)
{
    ASSERT_R_STR (pws);
    MCHECK_MEM_POINTER (pws)

    if (IsEmptyStr (pws))
        AddWChar ('\0');
    else
        Append (pws, (wcslen (pws) + 1) * sizeof (WCHAR));
}

void CVolMem::AddOnlyText (const WCHAR* pws)
{
    ASSERT_R_STR (pws);
    MCHECK_MEM_POINTER (pws)

    if (IsEmptyStr (pws) == FALSE)
        Append (pws, wcslen (pws) * sizeof (WCHAR));
}

void CVolMem::AddOnlyText (const U8CHAR* ps)
{
    ASSERT_R_STR (ps);
    MCHECK_MEM_POINTER (ps)

    if (IsEmptyStr (ps) == FALSE)
        Append (ps, strlen (ps) * sizeof (U8CHAR));
}

void CVolMem::AddString (const U8CHAR* ps)
{
    ASSERT_R_STR (ps);
    MCHECK_MEM_POINTER (ps)

    if (IsEmptyStr (ps))
        AddU8Char ('\0');
    else
        Append (ps, (strlen (ps) + 1) * sizeof (U8CHAR));
}

//---------------------------------------------------------

// if pData == NULL, insert blank data.
void CVolMem::Insert (const INT_P npOffset, const void* pData, const INT_P npSize)
{
#ifdef _DEBUG
    if (pData != NULL)
    {
        MCHECK_MEM_POINTER (pData)
        ASSERT (npOffset >= 0 && npOffset <= m_npSize);  // 插入偏移位置不应该超出已有数据尾部
        ASSERT_R_ADR (pData, npSize);
    }
#endif

    if (npSize <= 0)
        return;

    if (npOffset >= m_npSize)  // 在尾部插入?
    {
        Append (pData, npSize);
    }
    else  // 在中间插入
    {
        const INT_P npOldSize = m_npSize;

        BYTE* pInsertAt = Realloc (npOldSize + npSize) + npOffset;
        memmove (pInsertAt + npSize, pInsertAt, npOldSize - npOffset);

        if (pData != NULL)
            COPY_MEM (pInsertAt, pData, npSize);
        else
            ZERO_MEM (pInsertAt, npSize);
    }
}

// if pData == NULL, append blank data.
void CVolMem::Append (const void* pData, const INT_P npSize)
{
#ifdef _DEBUG
    if (pData != NULL)
    {
        MCHECK_MEM_POINTER (pData)
        ASSERT_R_ADR (pData, npSize);
    }
#endif

    if (m_npAllocedSize - m_npSize >= npSize)
    {
        if (npSize == (INT_P)sizeof (BYTE))
        {
            *(BYTE*)(m_pData + m_npSize++) = (pData == NULL ? 0 : *(BYTE*)pData);
            return;
        }
        else if (npSize == (INT_P)sizeof (WORD))
        {
            *(WORD*)(m_pData + m_npSize) = (pData == NULL ? 0 : *(WORD*)pData);
            m_npSize += (INT_P)sizeof (WORD);
            return;
        }
        else if (npSize == (INT_P)sizeof (DWORD))
        {
            *(DWORD*)(m_pData + m_npSize) = (pData == NULL ? 0 : *(DWORD*)pData);
            m_npSize += (INT_P)sizeof (DWORD);
            return;
        }
        else if (npSize == (INT_P)sizeof (UINT64))
        {
            *(UINT64*)(m_pData + m_npSize) = (pData == NULL ? 0 : *(UINT64*)pData);
            m_npSize += (INT_P)sizeof (UINT64);
            return;
        }
    }

    //-------------------------------------------------------------------

    if (npSize <= 0)
        return;

    const INT_P npOldSize = m_npSize;
    BYTE* pAppend = Realloc (npOldSize + npSize) + npOldSize;

    if (pData != NULL)
        COPY_MEM (pAppend, pData, npSize);
    else
        ZERO_MEM (pAppend, npSize);
}

// if pReplaceData == NULL, replace blank data.
void CVolMem::Replace (const INT_P npOffset, INT_P npSize, const void* pReplaceData, const INT_P npReplaceSize)
{
    MCHECK_MEM_POINTER (pReplaceData)
    ASSERT (npOffset >= 0 && npSize >= 0);
    ASSERT_R_ADR (pReplaceData, npReplaceSize);

    if (npOffset + npSize > m_npSize)
        npSize = m_npSize - npOffset;

    if (npSize <= 0)  // 欲替换数据为空?
    {
        Insert (npOffset, pReplaceData, npReplaceSize);  // 转为插入
        return;
    }

    if (npReplaceSize <= 0)  // 所提供数据为空?
    {
        Remove (npOffset, npSize);  // 转为删除
        return;
    }

    //---------------------------------------------

    const INT_P npOldSize = m_npSize;

    BYTE* pReplaceAt;
    const INT_P npMoveSize = npOldSize - npOffset - npSize;
    if (npReplaceSize > npSize)
    {
        pReplaceAt = Realloc (npOldSize + npReplaceSize - npSize) + npOffset;

        if (npMoveSize > 0)
            memmove (pReplaceAt + npReplaceSize, pReplaceAt + npSize, npMoveSize);
    }
    else
    {
        pReplaceAt = m_pData + npOffset;

        if (npReplaceSize < npSize)
        {
            if (npMoveSize > 0)
                memmove (pReplaceAt + npReplaceSize, pReplaceAt + npSize, npMoveSize);

            pReplaceAt = Realloc (npOldSize - (npSize - npReplaceSize)) + npOffset;
        }
    }

    if (pReplaceData != NULL)
        COPY_MEM (pReplaceAt, pReplaceData, npReplaceSize);
    else
        ZERO_MEM (pReplaceAt, npReplaceSize);
}

void CVolMem::Remove (const INT_P npOffset, const INT_P npSize)
{
    ASSERT (npOffset >= -1 && npSize >= 0);

    if (npSize <= 0)
        return;

    if (npOffset <= -1)  // 从尾部开始向前删除?
    {
        const INT_P npNewSize = m_npSize - npSize;

        if (npNewSize <= 0)  // 全部删除?
            Free ();
        else
            Realloc (npNewSize);  // 去除尾部所指定尺寸的数据
    }
    else
    {
        INT_P npRemoveSize;

        if (npSize < m_npSize - npOffset)  // 在中间删除?
        {
            BYTE* pRemoveAt = m_pData + npOffset;
            npRemoveSize = npSize;
            memmove (pRemoveAt, pRemoveAt + npRemoveSize, m_npSize - npOffset - npRemoveSize);
        }
        else
        {
            // 从npOffset一直删除到尾部
            npRemoveSize = m_npSize - npOffset;
        }

        if (m_npSize == npRemoveSize)
            Free ();
        else
            Realloc (m_npSize - npRemoveSize);
    }
}

INT_P CVolMem::ReadFromFile (const TCHAR* szFileName, INT_P npReadDataSize)
{
    ASSERT (npReadDataSize >= -1);
    ASSERT_R_STR (szFileName);

    if (IsEmptyStr (szFileName))
        return -1;

    INT_P npResult = -1;
    
    FILE* in = _tfopen (szFileName, _T ("rb"));
    if (in != NULL)
    {
        if (npReadDataSize == -1)
        {
            fseek (in, 0, SEEK_END);
            npReadDataSize = (INT_P)ftell (in);
            fseek (in, 0, SEEK_SET);
        }

        if (npReadDataSize > 0)
        {
            const INT_P npRealSize = fread (Alloc (npReadDataSize), 1, npReadDataSize, in);

            if (!ferror (in))
            {
                Realloc (npRealSize);  // 释放多余空间
                fclose (in);
                return npRealSize;
            }
        }
        else
        {
            npResult = 0;
        }

        fclose (in);
    }

    Free ();
    return npResult;
}

BOOL_P CVolMem::WriteIntoFile (const TCHAR* szFileName, INT_P npWriteDataSize) const
{
    ASSERT (npWriteDataSize >= -1);
    ASSERT_R_STR (szFileName);

    if (npWriteDataSize == -1 || npWriteDataSize > m_npSize)
        npWriteDataSize = m_npSize;

    return WriteDataIntoFile (szFileName, m_pData, npWriteDataSize);
}

CVolString CVolMem::Get_CVolString (const INT_P npOffset) const
{
    ASSERT (npOffset >= 0);

    CVolString str;

    if (npOffset + (INT_P)sizeof (TCHAR) <= m_npSize)  // 存在至少一个字符?
    {
        const TCHAR* psBegin = (const TCHAR*)(m_pData + npOffset);
        const TCHAR* psEndChar = (const TCHAR*)(m_pData + m_npSize) - 1;  // 获得字节集尾字符指针
        ASSERT (psBegin <= psEndChar);  // 前面检查过

        // 搜寻下一个零字符
        const TCHAR* ps = psBegin;
        while (ps <= psEndChar && *ps != '\0')
            ps++;

        str.AddText (psBegin, ps - psBegin);
    }

    return str;
}

void CVolMem::AddTextValue (const TCHAR* ps, const BOOL_P blpAddEndZeroChar)
{
    if (blpAddEndZeroChar)
        AddString (ps);
    else
        AddOnlyText (ps);
}

void CVolMem::InsertTextValue (const INT_P npOffset, const TCHAR* ps, const BOOL_P blpInsertEndZeroChar)
{
    if (blpInsertEndZeroChar)
        InsertString (npOffset, ps);
    else
        InsertOnlyText (npOffset, ps);
}

CVolMem CVolMem::GetBinMid (INT_P npOffset, INT_P npSize) const
{
    ASSERT (npOffset >= 0 && npSize >= 0);

    if (npOffset < m_npSize)
    {
        const INT_P npMaxSize = m_npSize - npOffset;
        if (npSize > npMaxSize)
            npSize = npMaxSize;

        return CVolMem (m_pData + npOffset, npSize);
    }

    return CVolMem ();
}

INT_P CVolMem::FindBin (const BYTE* pFindBin, const INT_P npFindBinSize, INT_P npBeginOffset) const
{
    ASSERT (npBeginOffset >= 0);
    ASSERT_R_ADR (pFindBin, npFindBinSize);

    if (npFindBinSize == 0)
        return -1;

    if (npBeginOffset > m_npSize)
        npBeginOffset = m_npSize;

    const BYTE* pb = m_pData + npBeginOffset;
    ASSERT (pFindBin != NULL);
    const BYTE btFirst = *pFindBin;

    const INT_P npMaxOffset = m_npSize - npFindBinSize;
    for (INT_P npOffset = npBeginOffset; npOffset <= npMaxOffset; npOffset++, pb++)
    {
        if (*pb == btFirst &&
                (npFindBinSize == 1 || memcmp (pb, pFindBin, npFindBinSize) == 0))
        {
            return npOffset;
        }
    }

    return -1;
}

INT_P CVolMem::ReverseFindBin (const BYTE* pFindBin, const INT_P npFindBinSize, INT_P npBeginOffset) const
{
    ASSERT (npBeginOffset >= 0);
    ASSERT_R_ADR (pFindBin, npFindBinSize);

    if (npFindBinSize == 0)
        return -1;

    if (npBeginOffset > m_npSize)
        npBeginOffset = m_npSize;

    npBeginOffset -= npFindBinSize;

    const BYTE* pb = m_pData + npBeginOffset;
    ASSERT (pFindBin != NULL);
    const BYTE btFirst = *pFindBin;

    for (INT_P npOffset = npBeginOffset; npOffset >= 0; npOffset--, pb--)
    {
        if (*pb == btFirst &&
                (npFindBinSize == 1 || memcmp (pb, pFindBin, npFindBinSize) == 0))
        {
            return npOffset;
        }
    }

    return -1;
}

void CVolMem::ReplaceBin (const BYTE* pFindBin, const INT_P npFindBinSize,
        const BYTE* pReplaceBin, const INT_P npReplaceBinSize, INT_P npBeginOffset, INT_P npReplaceTimes)
{
    ASSERT (npBeginOffset >= 0 && npReplaceTimes >= 0);
    ASSERT_R_ADR (pFindBin, npFindBinSize);
    ASSERT_R_ADR (pReplaceBin, npReplaceBinSize);

    if (npFindBinSize <= 0 || npBeginOffset >= m_npSize)
        return;

    ASSERT (pFindBin != NULL);
    const BYTE btFirst = *pFindBin;

    INT_P npMaxOffset = m_npSize - npFindBinSize;
    for (INT_P npOffset = npBeginOffset; npOffset <= npMaxOffset; )
    {
        if (m_pData [npOffset] == btFirst &&
                (npFindBinSize == 1 || memcmp (m_pData + npOffset, pFindBin, npFindBinSize) == 0))
        {
            Replace (npOffset, npFindBinSize, pReplaceBin, npReplaceBinSize);
            
            npOffset += npReplaceBinSize;
            npMaxOffset = m_npSize - npFindBinSize;

            npReplaceTimes--;
            if (npReplaceTimes == 0)
                break;
        }
        else
        {
            npOffset++;
        }
    }
}

INT_P CVolMem::SplitBin (const BYTE* pFindBin, const INT_P npFindBinSize, INT_P npMaxNumResultBin, CVolObjectArray& aryResultBin)
{
    ASSERT (npMaxNumResultBin >= 0);
    ASSERT_R_ADR (pFindBin, npFindBinSize);

    aryResultBin.RemoveAll ();

    if (npFindBinSize <= 0)
        return 0;

    ASSERT (pFindBin != NULL);
    const BYTE btFirst = *pFindBin;
    INT_P npLastOffset = 0;

    const INT_P npMaxOffset = m_npSize - npFindBinSize;
    INT_P npOffset = 0;
    while (TRUE)
    {
        if (npOffset > npMaxOffset)
        {
            ASSERT (npLastOffset <= m_npSize);
            ((CVolMem&)aryResultBin.AddNewObject (VOL_RUNTIME_CLASS (CVolMem), 0, NULL)).
                    Append (m_pData + npLastOffset, m_npSize - npLastOffset);

            break;
        }

        if (m_pData [npOffset] == btFirst &&
                (npFindBinSize == 1 || memcmp (m_pData + npOffset, pFindBin, npFindBinSize) == 0))
        {
            ASSERT (npOffset >= npLastOffset);
            ((CVolMem&)aryResultBin.AddNewObject (VOL_RUNTIME_CLASS (CVolMem), 0, NULL)).
                    Append (m_pData + npLastOffset, npOffset - npLastOffset);

            npOffset += npFindBinSize;
            npLastOffset = npOffset;

            npMaxNumResultBin--;
            if (npMaxNumResultBin == 0)
                break;
        }
        else
        {
            npOffset++;
        }
    }

    return aryResultBin.GetCount ();
}

HGLOBAL CVolMem::ToGlobalMem () const
{
    if (m_npSize == 0)
        return NULL;

    const HGLOBAL hGlobal = ::GlobalAlloc ((GMEM_MOVEABLE | GMEM_NODISCARD), (SIZE_T)m_npSize);
    if (hGlobal == NULL)
        return NULL;

    void* pbDest = ::GlobalLock (hGlobal);
    if (pbDest == NULL)
    {
        ::GlobalFree (hGlobal);
        return NULL;
    }

    COPY_MEM (pbDest, m_pData, m_npSize);
    ::GlobalUnlock (hGlobal);

    return hGlobal;
}

CVolString& CVolMem::ToHexStr (CVolString& strResult)
{
    CVolMem memResult;
    TCHAR* psBegin = (TCHAR*)memResult.Alloc ((m_npSize * 2 + 3) * sizeof (TCHAR));
    *psBegin = '\0';

    TCHAR* ps = psBegin;
    const BYTE* pb = m_pData;

    for (INT_P npIndex = 0; npIndex < m_npSize; npIndex++, pb++)
    {
        ASSERT (memResult.IsInside (ps, sizeof (TCHAR) * 3));

        _stprintf (ps, _T ("%02X"), (DWORD)*pb);
        ps++;
        ps++;
    }
    ASSERT (IsAtEnd (pb));

    strResult.SetText (psBegin);
    return strResult;
}

CVolMem& CVolMem::AppendFromHexStr (const TCHAR* szHexStr)
{
    ASSERT_R_STR_OR_NULL (szHexStr);

    if (IsEmptyStr (szHexStr) == FALSE)
    {
        const INT_P npNumNewBytes = _tcslen (szHexStr) / 2;

        if (npNumNewBytes > 0)
        {
            BYTE* pb = (BYTE*)AddSpace (npNumNewBytes, TRUE);

            const TCHAR* ps = szHexStr;
            for (INT_P npIndex = 0; npIndex < npNumNewBytes; npIndex++, ps += 2)
                *pb++ = (BYTE)((HexCharToValue (ps [0]) << 4) | HexCharToValue (ps [1]));

            ASSERT (IsAtEnd (pb) && ps <= szHexStr + _tcslen (szHexStr));
        }
    }

    return *this;
}

void CVolMem::LoadFromStream (CVolBaseInputStream& stream)
{
    BaseClass::LoadFromStream (stream);

    INT nSize;
    if (stream.ReadExact (&nSize, sizeof (INT)))  // 读入数据尺寸成功?
    {
        if (nSize < 0)  // 数据尺寸错误?
        {
            stream.SetErrorCode (VESC_READ_ERR);
        }
        else if (nSize == 0)  // 数据尺寸为0?
        {
            Free ();
        }
        else
        {
            if (stream.ReadExact (Alloc (nSize), nSize) == FALSE)  // 读入数据失败?
                Free ();
        }
    }
}

void CVolMem::SaveIntoStream (CVolBaseOutputStream& stream)
{
    BaseClass::SaveIntoStream (stream);

    const INT nSize = (INT)GetSize ();
    stream.write (&nSize, sizeof (INT));
    stream.write (GetPtr (), nSize);
}
