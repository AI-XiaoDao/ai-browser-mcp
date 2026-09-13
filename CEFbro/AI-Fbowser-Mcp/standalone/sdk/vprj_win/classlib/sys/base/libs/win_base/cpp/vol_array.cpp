
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

#ifdef _DEBUG
    #define MCHECK_MEM_POINTER(p)  \
        if ((BYTE*)(p) >= m_mem.GetPtr () && (BYTE*)(p) < m_mem.GetPtr () + m_mem.GetSize ())  \
            ASSERT (FALSE);
#else
    #define MCHECK_MEM_POINTER(p)
#endif

WCHAR* CMStringArray::CloneText (const WCHAR* wszText, const INT_P npLen)
{
    // 如果wszText为NULL,则必须返回NULL,否则会导致程序其它位置释放所复制的指针错误.
    if (wszText == NULL || npLen <= 0)
        return NULL;
    ASSERT_R_STR2 (wszText, npLen);

    WCHAR* wszNew = (WCHAR*)mgrAlloc ((npLen + 1) * sizeof (WCHAR));
    COPY_MEM (wszNew, wszText, npLen * sizeof (WCHAR));
    wszNew [npLen] = '\0';

    return wszNew;
}

U8CHAR* CMStringArray::CloneText (const U8CHAR* szText, const INT_P npLen)
{
    // 如果szText为NULL,则必须返回NULL,否则会导致程序其它位置释放所复制的指针错误.
    if (szText == NULL || npLen <= 0)
        return NULL;
    ASSERT_R_STR2 (szText, npLen);

    U8CHAR* szNew = (U8CHAR*)mgrAlloc ((npLen + 1) * sizeof (U8CHAR));
    COPY_MEM (szNew, szText, npLen * sizeof (U8CHAR));
    szNew [npLen] = '\0';

    return szNew;
}

void CMStringArray::XchgElement (const INT_P npIndex1, const INT_P npIndex2)
{
    ASSERT (IsIndexValid (npIndex1) && IsIndexValid (npIndex2));

    TCHAR** pps = GetData ();

    TCHAR* ps = pps [npIndex1];
    pps [npIndex1] = pps [npIndex2];
    pps [npIndex2] = ps;
}

void CMStringArray::Append (const CMStringArray& src)
{
    MCHECK_MEM_POINTER (src.m_mem.GetPtr ())

    if (&src.m_mem == &m_mem)
    {
        FAIL;
        return;
    }

    const TCHAR** ppsAppend = src.GetData ();
    const INT_P npAppendCount = src.GetCount ();

    const INT_P npOldCount = GetCount ();
    m_mem.Append (NULL, npAppendCount * sizeof (TCHAR*));

    TCHAR** pps = GetData () + npOldCount;
    for (INT_P i = 0; i < npAppendCount; i++)
        pps [i] = CloneText (ppsAppend [i]);
}

void CMStringArray::UniqueAppend (const CMStringArray& src)
{
    if (&src.m_mem == &m_mem)
    {
        FAIL;
        return;
    }

    const INT_P npCount = src.GetCount ();
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
    {
        const TCHAR* ps = src.GetAt (npIndex);

        if (IsElementExist (ps) == FALSE)
            Add (ps);
    }
}

void CMStringArray::IUniqueAppend (const CMStringArray& src)
{
    if (&src.m_mem == &m_mem)
    {
        FAIL;
        return;
    }

    const INT_P npCount = src.GetCount ();
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
    {
        const TCHAR* ps = src.GetAt (npIndex);

        if (IIsElementExist (ps) == FALSE)
            Add (ps);
    }
}

void CMStringArray::RemoveDuplicated (const CMStringArray& saryTest)
{
    if (&saryTest.m_mem == &m_mem)
    {
        FAIL;
        return;
    }

    if (saryTest.IsEmpty ())
        return;

    const INT_P npCount = GetCount ();
    for (INT_P npIndex = npCount - 1; npIndex >= 0; npIndex--)
    {
        if (saryTest.IsElementExist (GetAt (npIndex)))
            RemoveAt (npIndex);
    }
}

void CMStringArray::IRemoveDuplicated (const CMStringArray& saryTest)
{
    if (&saryTest.m_mem == &m_mem)
    {
        FAIL;
        return;
    }

    if (saryTest.IsEmpty ())
        return;

    const INT_P npCount = GetCount ();
    for (INT_P npIndex = npCount - 1; npIndex >= 0; npIndex--)
    {
        if (saryTest.IIsElementExist (GetAt (npIndex)))
            RemoveAt (npIndex);
    }
}

void CMStringArray::RemoveAll ()
{
    TCHAR** pps = GetData ();
    const INT_P npCount = GetCount ();
    for (INT_P i = 0; i < npCount; i++)
    {
        if (pps [i] != NULL)
            mgrFree (pps [i]);
    }

    m_mem.Free ();
}

void CMStringArray::RemoveAt (const INT_P npIndex, const INT_P npCount)
{
    ASSERT (npIndex >= 0 && npCount >= 0 && npIndex + npCount <= GetCount ());

    TCHAR** pps = GetData () + npIndex;
    for (INT_P i = 0; i < npCount; i++)
    {
        if (pps [i] != NULL)
            mgrFree (pps [i]);
    }

    m_mem.Remove (npIndex * sizeof (TCHAR*), sizeof (TCHAR*) * npCount);
}

BOOL_P CMStringArray::RemoveElement (const TCHAR* ps)
{
    ASSERT_R_STR_OR_NULL (ps);

    const INT_P npIndex = FindFirstElement (ps);

    if (npIndex != -1)
    {
        RemoveAt (npIndex, 1);
        return TRUE;
    }

    return FALSE;
}

void CMStringArray::SetAt_NotClone (const INT_P npIndex, const TCHAR* szElement)
{
    MCHECK_MEM_POINTER (szElement)
    ASSERT (npIndex >= 0 && npIndex < GetCount ());
    ASSERT_R_STR_OR_NULL (szElement);

    TCHAR** pps = GetData () + npIndex;
    if (*pps != NULL)
        mgrFree ((void*)*pps);
    *pps = (TCHAR*)szElement;
}

INT_P CMStringArray::FindFirstElement (const TCHAR* ps) const
{
    if (ps != NULL)
    {
        ASSERT_R_STR (ps);

        const INT_P npCount = GetCount ();
        for (INT_P i = 0; i < npCount; i++)
        {
            if (_tcscmp (GetAt (i), ps) == 0)
                return i;
        }
    }

    return -1;
}

INT_P CMStringArray::FindLastElement (const TCHAR* ps) const
{
    if (ps != NULL)
    {
        ASSERT_R_STR (ps);

        const INT_P npCount = GetCount ();
        for (INT_P i = npCount - 1; i >= 0; i--)
        {
            if (_tcscmp (GetAt (i), ps) == 0)
                return i;
        }
    }

    return -1;
}

INT_P CMStringArray::IFindFirstElement (const TCHAR* ps) const
{
    if (ps != NULL)
    {
        ASSERT_R_STR (ps);

        const INT_P npCount = GetCount ();
        for (INT_P i = 0; i < npCount; i++)
        {
            if (_tcsicmp (GetAt (i), ps) == 0)
                return i;
        }
    }

    return -1;
}

INT_P CMStringArray::IFindLastElement (const TCHAR* ps) const
{
    if (ps != NULL)
    {
        ASSERT_R_STR (ps);

        const INT_P npCount = GetCount ();
        for (INT_P i = npCount - 1; i >= 0; i--)
        {
            if (_tcsicmp (GetAt (i), ps) == 0)
                return i;
        }
    }

    return -1;
}

BOOL_P CMStringArray::ReplaceAllElements (const TCHAR* szOldText, const TCHAR* szNewText)
{
    ASSERT_R_STR_OR_NULL (szOldText);
    ASSERT_R_STR_OR_NULL (szNewText);

    BOOL_P blpReplaced = FALSE;

    const INT_P npCount = GetCount ();
    for (INT_P i = 0; i < npCount; i++)
    {
        if (_tcscmp (GetAt (i), szOldText) == 0)
        {
            SetAt (i, szNewText);
            blpReplaced = TRUE;
        }
    }

    return blpReplaced;
}

BOOL_P CMStringArray::IReplaceAllElements (const TCHAR* szOldText, const TCHAR* szNewText)
{
    ASSERT_R_STR_OR_NULL (szOldText);
    ASSERT_R_STR_OR_NULL (szNewText);

    BOOL_P blpReplaced = FALSE;

    const INT_P npCount = GetCount ();
    for (INT_P i = 0; i < npCount; i++)
    {
        if (_tcsicmp (GetAt (i), szOldText) == 0)
        {
            SetAt (i, szNewText);
            blpReplaced = TRUE;
        }
    }

    return blpReplaced;
}

BOOL_P CMStringArray::IsEqual (const CMStringArray& sary, const BOOL_P blpIgnoreCase) const
{
    if (&sary.m_mem == &m_mem)
        return TRUE;

    const INT_P npCount = GetCount ();
    if (sary.GetCount () != npCount)
        return FALSE;

    for (INT_P i = 0; i < npCount; i++)
    {
        if (blpIgnoreCase)  // 忽略大小写?
        {
            if (_tcsicmp (GetAt (i), sary.GetAt (i)) != 0)
                return FALSE;
        }
        else
        {
            if (_tcscmp (GetAt (i), sary.GetAt (i)) != 0)
                return FALSE;
        }
    }

    return TRUE;
}

CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, CMStringArray& strary)
{
    strary.LoadFromStream (stream);
    return stream;
}

CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const CMStringArray& strary)
{
    ((CMStringArray&)strary).SaveIntoStream (stream);
    return stream;
}

void CMStringArray::LoadFromStream (CVolBaseInputStream& stream)
{
    RemoveAll ();

    INT nCount;
    stream >> nCount;

    if (stream.IsSucceeded ())
    {
        CVolString str;
        for (INT_P i = 0; i < nCount; i++)
        {
            str.LoadFromStream (stream);
            if (stream.IsFoundError ())
                break;
            Add (str.GetText ());
        }
    }
}

void CMStringArray::SaveIntoStream (CVolBaseOutputStream& stream)
{
    const INT_P npCount = GetCount ();
    stream << (INT)npCount;

    for (INT_P i = 0; i < npCount; i++)
    {
        CVolString (GetAt (i)).SaveIntoStream (stream);
    }
}

void CMStringArray::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    if (nMaxDumpSize == 0)  // 使用默认尺寸?
        nMaxDumpSize = 64;

    const INT_P npCount = GetCount ();
    const INT_P npDumpedCount = (nMaxDumpSize < 0 ? npCount : MIN (npCount, nMaxDumpSize));

    if (npCount == npDumpedCount)
        strDump.AddFormatText (_T_ARY_ELEMENTS_DUMPED1_D, (INT)npCount);
    else
        strDump.AddFormatText (_T_ARY_ELEMENTS_DUMPED2_DDD, (INT)npCount, npDumpedCount, (INT)(npCount - npDumpedCount));

    CVolString strBuf;
    for (INT_P npIndex = 0; npIndex < npDumpedCount; npIndex++)
        strDump.AddFormatText (_T ("\r\n%d. %s"), (INT)(npIndex + 1), MakeStringFromPlainText (GetAt (npIndex), &strBuf, TRUE));
}

//----------------------------------------------------------------------------

CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, CMStringSortArray& ary)
{
    stream >> ary.m_sary;
    return stream;
}

CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const CMStringSortArray& ary)
{
    stream << ary.m_sary;
    return stream;
}

void CMStringSortArray::LoadFromStream (CVolBaseInputStream& stream)
{
    m_sary.LoadFromStream (stream);
}

void CMStringSortArray::SaveIntoStream (CVolBaseOutputStream& stream)
{
    m_sary.SaveIntoStream (stream);
}

INT_P CMStringSortArray::Add (const TCHAR* data, const BOOL_P blpAddAtEnd)
{
    ASSERT_R_STR_OR_NULL (data);

    const TCHAR** ary = GetData ();
    INT_P npLowIndex;
    INT_P npHighIndex = GetCount () - 1;

    if (npHighIndex < 0 ||
            compare (data, ary [0]) < 0)
    {
        npLowIndex = 0;
    }
    else if (compare (data, ary [npHighIndex]) > 0)
    {
        npLowIndex = npHighIndex + 1;
    }
    else
    {
        npLowIndex = 0;

        while (npLowIndex <= npHighIndex)
        {
            const INT_P npMidIndex = (npHighIndex + npLowIndex) / 2;
            const INT_P npCompareResult = compare (data, ary [npMidIndex]);

            if (npCompareResult == 0)
            {
                if (blpAddAtEnd == FALSE)  // 不要求加入到同等成员的尾部?
                {
                    npLowIndex = npMidIndex;
                    break;
                }
                else  // 加入到同等成员的尾部
                {
                    npLowIndex = npMidIndex + 1;
                    if (npLowIndex > npHighIndex || compare (data, ary [npLowIndex]) != 0)
                        break;
                }
            }
            else if (npCompareResult > 0)
                npLowIndex = npMidIndex + 1;
            else
                npHighIndex = npMidIndex - 1;
        }
    }

    m_sary.InsertAt (npLowIndex, data);
    return npLowIndex;
}

INT_P CMStringSortArray::FindElement (const TCHAR* data) const
{
    ASSERT_R_STR_OR_NULL (data);

    const TCHAR** ary = GetData ();
    INT_P npHighIndex = GetCount () - 1;

    if (npHighIndex < 0 ||
            compare (data, ary [0]) < 0 ||
            compare (data, ary [npHighIndex]) > 0)
    {
        return -1;
    }

    INT_P npLowIndex = 0;
    while (npLowIndex <= npHighIndex)
    {
        const INT_P npMidIndex = (npHighIndex + npLowIndex) / 2;
        const INT_P npCompareResult = compare (data, ary [npMidIndex]);

        if (npCompareResult == 0)
            return npMidIndex;

        // data > ary [npMidIndex] 表明要求查找的值在[npMidIndex+1,npHighIndex],否则,在[npLowIndex,npMidIndex-1]
        if (npCompareResult > 0)
            npLowIndex = npMidIndex + 1;
        else
            npHighIndex = npMidIndex - 1;
    }

    return -1;
}

// 使用希尔排序法重新排序
void CMStringSortArray::Sort ()
{
    const TCHAR** pElement = GetData ();
    const INT_P npCount = GetCount ();

    INT_P npIndex = npCount / 2;
    while (npIndex >= 1)
    {
        for (INT_P i = npIndex; i < npCount; i++)
        {
            const TCHAR* temp = pElement [i];

            INT_P j;
            for (j = i - npIndex; j >= 0 && compare (temp, pElement [j]) < 0; j -= npIndex)
            {
                ASSERT (j + npIndex >= 0 && j + npIndex < npCount && j >= 0 && j < npCount);
                pElement [j + npIndex] = pElement [j];
            }

            ASSERT (j + npIndex >= 0 && j + npIndex < npCount);
            pElement [j + npIndex] = temp;
        }

        npIndex /= 2;
    }
}

void CMStringSortArray::SortAndEnsureUnique ()
{
    Sort ();  // 首先排序

    // 然后逆向顺序删除重复的项目
    const INT_P npCount = GetCount ();
    for (INT_P npIndex = npCount - 1; npIndex > 0; npIndex--)
    {
        if (compare (GetAt (npIndex), GetAt (npIndex - 1)) == 0)  // 与上一个成员相同?
            RemoveAt (npIndex);
    }
}

INT_P CMStringSortArray::FindFirstElement (const TCHAR* data) const
{
    ASSERT_R_STR_OR_NULL (data);

    INT_P npIndex = FindElement (data);
    if (npIndex == -1)
        return -1;

    npIndex--;

    const TCHAR** ary = GetData ();
    while (npIndex >= 0)
    {
        if (compare (data, ary [npIndex]) != 0)
            break;
        npIndex--;
    }

    return npIndex + 1;
}

INT_P CMStringSortArray::FindLastElement (const TCHAR* data) const
{
    ASSERT_R_STR_OR_NULL (data);

    INT_P npIndex = FindElement (data);
    if (npIndex == -1)
        return -1;

    npIndex++;

    const TCHAR** ary = GetData ();
    const INT_P npCount = GetCount ();
    while (npIndex < npCount)
    {
        if (compare (data, ary [npIndex]) != 0)
            break;
        npIndex++;
    }

    return npIndex - 1;
}

BOOL_P CMStringSortArray::IsEqual (const CMStringSortArray& sary) const
{
    if (&sary.m_sary == &m_sary)
        return TRUE;

    const INT_P npCount = GetCount ();
    if (sary.GetCount () != npCount)
        return FALSE;

    for (INT_P i = 0; i < npCount; i++)
    {
        if (compare (GetAt (i), sary.GetAt (i)) != 0)
            return FALSE;
    }

    return TRUE;
}

//----------------------------------------------------------------------------

INT_P CUniqueStringArray::Add (const TCHAR* data, INT_P* pnpExistElementIndex)
{
    ASSERT_R_STR_OR_NULL (data);
#ifdef _DEBUG
    if (pnpExistElementIndex != NULL)
        ASSERT_RW_DATA (pnpExistElementIndex);
#endif

    const TCHAR** ary = GetData ();
    INT_P npLowIndex;
    INT_P npHighIndex = GetCount () - 1;

    if (npHighIndex < 0 ||
            compare (data, ary [0]) < 0)
    {
        npLowIndex = 0;
    }
    else if (compare (data, ary [npHighIndex]) > 0)
    {
        npLowIndex = npHighIndex + 1;
    }
    else
    {
        npLowIndex = 0;

        while (npLowIndex <= npHighIndex)
        {
            const INT_P npMidIndex = (npHighIndex + npLowIndex) / 2;
            const INT_P npCompareResult = compare (data, ary [npMidIndex]);

            if (npCompareResult == 0)
            {
                if (pnpExistElementIndex != NULL)
                    *pnpExistElementIndex = npMidIndex;
                return -1;
            }
            if (npCompareResult > 0)
                npLowIndex = npMidIndex + 1;
            else
                npHighIndex = npMidIndex - 1;
        }
    }

    m_sary.InsertAt (npLowIndex, data);
    if (pnpExistElementIndex != NULL)
        *pnpExistElementIndex = npLowIndex;
    return npLowIndex;
}

//-----------------------------------------------------------------------------------------------------

void CVolObjectArray::_CopySelfFrom (const CVolObjectArray& objCopyFrom)
{
    if (&objCopyFrom.m_arypObjects != &m_arypObjects)
    {
        RemoveAll ();
        Append (objCopyFrom);
    }
    ELSE_FAIL
}

BOOL CVolObjectArray::_IsSelfEqual (const CVolObjectArray& objCompare) const
{
    const INT_P npCount = GetCount ();
    if (objCompare.GetCount () != npCount)
        return FALSE;

    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
    {
        if (m_arypObjects.GetAt (npIndex)->IsVolObjectEqual (*objCompare.m_arypObjects.GetAt (npIndex)) == FALSE)
            return FALSE;
    }

    return TRUE;
}

void CVolObjectArray::RemoveAll ()
{
    const INT_P npCount = m_arypObjects.GetCount ();
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
        m_arypObjects [npIndex]->Destroy ();

    m_arypObjects.RemoveAll ();
}

void CVolObjectArray::Append (const CVolObjectArray& src)
{
    if (&src.m_arypObjects == &m_arypObjects)
    {
        FAIL;
        return;
    }

    const INT_P npCount = src.m_arypObjects.GetCount ();
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
        m_arypObjects.Add (src.m_arypObjects [npIndex]->MakeCloneObject ());
}

void CVolObjectArray::RemoveAt (const INT_P npIndex, const INT_P npCount)
{
    ASSERT (npIndex >= 0 && npCount >= 0 && npIndex + npCount <= GetCount ());

    for (INT_P i = 0; i < npCount; i++)
        m_arypObjects [npIndex + i]->Destroy ();

    m_arypObjects.RemoveAt (npIndex, npCount);
}

void CVolObjectArray::SetAt (const INT_P npIndex, const CVolObject& obj)
{
    ASSERT (IsIndexValid (npIndex));

    CVolObject* pOldObject = m_arypObjects [npIndex];
    m_arypObjects.SetAt (npIndex, obj.MakeCloneObject ());
    pOldObject->Destroy ();
}

INT_P CVolObjectArray::Add (const CVolObject& obj, CVolObject** ppNewVolObject)
{
    CVolObject* pNewVolObject = obj.MakeCloneObject ();
    if (ppNewVolObject != NULL)
    {
        ASSERT_RW_DATA (ppNewVolObject);
        *ppNewVolObject = pNewVolObject;
    }

    return m_arypObjects.Add2 (pNewVolObject);
}

INT_P CVolObjectArray::AddNewObject (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue)
{
    ASSERT_R_DATA (pRuntimeClass);

    CVolObject* pNewVolObject = pRuntimeClass->CreateObject ();
    pNewVolObject->m_npUserValue = npUserValue;

    return m_arypObjects.Add2 (pNewVolObject);
}

CVolObject& CVolObjectArray::AddNewObject (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue, INT* pnElementIndex)
{
    ASSERT_R_DATA (pRuntimeClass);

    CVolObject* pNewVolObject = pRuntimeClass->CreateObject ();
    pNewVolObject->m_npUserValue = npUserValue;

    if (pnElementIndex != NULL)
        *pnElementIndex = (INT)m_arypObjects.Add2 (pNewVolObject);
    else
        m_arypObjects.Add (pNewVolObject);

    return *pNewVolObject;
}

INT_P CVolObjectArray::AddNewObjects (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue, const INT_P npNumNewObjects)
{
    ASSERT_R_DATA (pRuntimeClass);

    const INT_P npCount = m_arypObjects.GetCount ();

    if (npNumNewObjects > 0)
    {
        CVolObject** apObjects = m_arypObjects.AddEmptyElements (npNumNewObjects, FALSE);

        for (INT_P npIndex = 0; npIndex < npNumNewObjects; npIndex++)
        {
            apObjects [npIndex] = pRuntimeClass->CreateObject ();
            apObjects [npIndex]->m_npUserValue = npUserValue;
        }
    }

    return npCount;
}

INT_P CVolObjectArray::AddTakeOverObject (CVolObject* pVolObject)
{
    ASSERT (pVolObject != NULL);

    return m_arypObjects.Add2 (pVolObject);
}

CVolObject& CVolObjectArray::InsertAt (const INT_P npIndex, const CVolObject& obj)
{
    ASSERT (npIndex >= 0 && npIndex <= GetCount ());

    CVolObject* pNewVolObject = obj.MakeCloneObject ();
    m_arypObjects.InsertAt (npIndex, pNewVolObject);

    return *pNewVolObject;
}

CVolObject& CVolObjectArray::InsertNewObject (const INT_P npIndex, const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue)
{
    ASSERT (npIndex >= 0 && npIndex <= GetCount ());
    ASSERT_R_DATA (pRuntimeClass);

    CVolObject* pNewVolObject = pRuntimeClass->CreateObject ();
    pNewVolObject->m_npUserValue = npUserValue;

    m_arypObjects.InsertAt (npIndex, pNewVolObject);

    return *pNewVolObject;
}

void CVolObjectArray::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    const INT nOldMaxDumpSize = nMaxDumpSize;

    if (nMaxDumpSize == 0)  // 使用默认尺寸?
        nMaxDumpSize = 64;

    const INT_P npCount = GetCount ();
    const INT_P npDumpedCount = (nMaxDumpSize < 0 ? npCount : MIN (npCount, nMaxDumpSize));

    if (npCount == npDumpedCount)
        strDump.AddFormatText (_T_ARY_ELEMENTS_DUMPED1_D, (INT)npCount);
    else
        strDump.AddFormatText (_T_ARY_ELEMENTS_DUMPED2_DDD, (INT)npCount, npDumpedCount, (INT)(npCount - npDumpedCount));

    for (INT_P npIndex = 0; npIndex < npDumpedCount; npIndex++)
    {
        CVolObject& obj = GetAt (npIndex);

        strDump.AddFormatText (_T_VOL_OBJECT_DSX, (INT)(npIndex + 1), CVolString (obj.GetRuntimeClass ()->GetClassFullName ()).GetText (), (UINT_P)&obj);

        if (obj.IsNullObject ())
            strDump.AddText (_T_EMPTY_VOL_OBJECT);

        strDump.AddText (_T_VOL_OBJECT_CONTENT);

        CVolString str;
        obj.GetDumpString (str, nOldMaxDumpSize);
        strDump.AddText (str);
    }
}
