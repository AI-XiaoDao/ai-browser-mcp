
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

BOOL_P CVBaseInputStream::close ()
{
    if (CVBaseStream::close () == FALSE)
        return FALSE;

    m_pBufCurrentData = m_pBufValidDataEnd = m_pBufBegin;  // 重新置位缓冲区
    m_npReadedDataSize = 0;

    return TRUE;
}

void CVBaseInputStream::_cleanup ()
{
    close ();
        
    if (m_pBufBegin != NULL)
    {
        mgrFree (m_pBufBegin);
        m_pBufBegin = NULL;
    }
}

void CVBaseInputStream::_reset (const INT_P npBufSize)
{
    ASSERT (m_pBufBegin == NULL);

    if (npBufSize > 0)
    {
        m_pBufBegin = (BYTE*)mgrAlloc (npBufSize);

        if (m_pBufBegin != NULL)
            m_npBufSize = npBufSize;
        else
            m_npBufSize = 0;

        m_pBufCurrentData = m_pBufValidDataEnd = m_pBufBegin;
    }
    else
    {
        m_pBufBegin = m_pBufCurrentData = m_pBufValidDataEnd = NULL;
        m_npBufSize = 0;
    }

    m_npReadedDataSize = 0;
}

INT_P CVBaseInputStream::_read (void* buf, const INT_P npSize)
{
    if (IsFoundError () || npSize <= 0)
        return 0;
    ASSERT_RW_ADR (buf, npSize);

    if (m_npBufSize == 0)  // 没有缓冲区?
        return _real_read (buf, npSize);

    //-------------------------------------------------

    BYTE* pBuf = (BYTE*)buf;
    INT_P npAlreadyReadedSize = 0;

    const INT_P npBufValidDataSize = m_pBufValidDataEnd - m_pBufCurrentData;
    if (npBufValidDataSize > 0)  // 当前缓冲区中是否有数据?
    {
        npAlreadyReadedSize = MIN (npSize, npBufValidDataSize);
        COPY_MEM (pBuf, m_pBufCurrentData, npAlreadyReadedSize);  // 将缓冲区中的数据拷贝出来
        
        m_pBufCurrentData += npAlreadyReadedSize;  // 移动当前数据指针

        if (npAlreadyReadedSize == npSize)
            return npSize;

        pBuf += npAlreadyReadedSize;
    }

    ASSERT (m_pBufCurrentData == m_pBufValidDataEnd);  // 到此处缓冲区必定已经为空

    //-------------------------------------------------

    ASSERT (m_pBufCurrentData == m_pBufValidDataEnd);  // 缓冲区中的数据必定已经被使用完毕
    ASSERT (npAlreadyReadedSize < npSize);

    const INT_P npLastReadSize = (npSize - npAlreadyReadedSize) % m_npBufSize;  // 计算需要在最后一次读取到缓冲区内的数据尺寸
    if (npLastReadSize == 0)  // 如果为0，表明没有多余数据，可以不通过缓冲区直接读取. 
        return npAlreadyReadedSize + _real_read (pBuf, npSize - npAlreadyReadedSize);

    // 计算超出缓冲区尺寸需要首先直接读取的数据部分尺寸
    const INT_P npFirstReadSize = npSize - npAlreadyReadedSize - npLastReadSize;
    if (npFirstReadSize > 0)
    {
        const INT_P np = _real_read (pBuf, npFirstReadSize);
        if (np != npFirstReadSize)
            return npAlreadyReadedSize + np;
        pBuf += npFirstReadSize;
        npAlreadyReadedSize += npFirstReadSize;
    }

    //-------------------------------------------------

    const INT_P npDataSizeInBuf = _real_read (m_pBufBegin, m_npBufSize);  // 一次性读取一个缓冲区

    const INT_P np = MIN (npLastReadSize, npDataSizeInBuf);  // 计算用户数据尺寸并拷贝过去
    COPY_MEM (pBuf, m_pBufBegin, np);
    npAlreadyReadedSize += np;

    m_pBufCurrentData = m_pBufBegin + np;
    m_pBufValidDataEnd = m_pBufBegin + npDataSizeInBuf;

    return npAlreadyReadedSize;
}

BOOL_P CVBaseInputStream::_skip (INT_P npSize)
{
    ASSERT (npSize >= 0);

    if (IsFoundError ())
        return FALSE;

    if (npSize == 0)
        return TRUE;

    if (npSize < 0)
    {
        SetErrorCode (VESC_SEEK_ERR);
        return FALSE;
    }

    const INT_P npBufValidDataSize = m_pBufValidDataEnd - m_pBufCurrentData;
    if (npBufValidDataSize > 0)  // 当前缓冲区中是否有数据?
    {
        const INT_P np = MIN (npSize, npBufValidDataSize);
        npSize -= np;
        m_pBufCurrentData += np;
    }

    if (npSize > 0 && real_skip (npSize) == FALSE)
    {
        SetErrorCode (VESC_SEEK_ERR);
        return FALSE;
    }

    return TRUE;
}

BOOL_P CVBaseInputStream::eof () const
{
    if (IsFoundError ())
        return TRUE;

    return (m_pBufValidDataEnd > m_pBufCurrentData ? FALSE : real_eof ());
}

INT_P CVBaseInputStream::ReadToEnd (CVolMem& mem)
{
    const INT_P npOldSize = mem.GetSize ();

    BYTE buf [0x1000];
    while (eof () == FALSE)
        mem.Append (buf, read (buf, sizeof (buf)));

    return mem.GetSize () - npOldSize;
}

//----------------------------------------------------------------------

BOOL_P CVBaseOutputStream::close ()
{
    const BOOL_P blpSucceeded = flush ();

    return CVBaseStream::close () && blpSucceeded;
}

void CVBaseOutputStream::_cleanup ()
{
    close ();

    if (m_pBufBegin != NULL)
    {
        mgrFree (m_pBufBegin);
        m_pBufBegin = NULL;
    }
}

void CVBaseOutputStream::_reset (const INT_P npBufSize)
{
    ASSERT (m_pBufBegin == NULL);

    if (npBufSize > 0)
    {
        m_pBufBegin = (BYTE*)mgrAlloc (npBufSize);
        if (m_pBufBegin != NULL)
            m_pBufEnd = m_pBufBegin + npBufSize;
        else
            m_pBufEnd = NULL;

        m_pBufCurrent = m_pBufBegin;
    }
    else
        m_pBufBegin = m_pBufEnd = m_pBufCurrent = NULL;
}

BOOL_P CVBaseOutputStream::flush ()
{
    if (IsFoundError ())
        return FALSE;

    if (m_pBufCurrent > m_pBufBegin)
    {
        if (real_write (m_pBufBegin, m_pBufCurrent - m_pBufBegin) == FALSE)
        {
            SetErrorCode (VESC_WRITE_ERR);
            return FALSE;
        }

        m_pBufCurrent = m_pBufBegin;
    }

    return TRUE;
}

BOOL_P CVBaseOutputStream::_write (const void* pBuf, const INT_P npSize)
{
    ASSERT_R_ADR (pBuf, npSize);

    if (IsFoundError ())
        return FALSE;

    if (npSize == 0)
        return TRUE;

    if (m_pBufEnd - m_pBufCurrent >= npSize)
    {
        COPY_MEM (m_pBufCurrent, pBuf, npSize);
        m_pBufCurrent += npSize;
    }
    else
    {
        if (flush () == FALSE)
            return FALSE;

        if (m_pBufEnd - m_pBufCurrent >= npSize)
        {
            COPY_MEM (m_pBufCurrent, pBuf, npSize);
            m_pBufCurrent += npSize;
        }
        else
        {
            if (real_write (pBuf, npSize) == FALSE)
            {
                SetErrorCode (VESC_WRITE_ERR);
                return FALSE;
            }
        }
    }

    return TRUE;
}

INT_P CVBaseFile::ReadToEnd (CVolMem& mem)
{
    const INT_P npSize = GetSize () - tell ();  // 获得当前文件指针后的数据尺寸
    if (npSize <= 0)  // 该数据尺寸小于等于0?
        return 0;

    const INT_P npReadLength = read (mem.AddSpace (npSize, FALSE), npSize);  // 分配空间并读入
    if (npReadLength != npSize)  // 所读入数据尺寸不等于期望尺寸?
        mem.Realloc (mem.GetSize () - npSize + npReadLength);  // 调整空间

    return npReadLength;
}

//----------------------------------------------------------------------

BOOL_P CVDiskFile::open (const TCHAR* szFileName, const VOL_FILE_OPEN_MODE enOpenMode)
{
    ASSERT_R_STR (szFileName);

    close ();

    if (IsEmptyStr (szFileName))
        return FALSE;

    const TCHAR* szMode =
            (enOpenMode == VFOM_READ ? _T ("rb") :
            enOpenMode == VFOM_WRITE ? _T ("wb") :
            enOpenMode == VFOM_APPEND ? _T ("ab") :
            NULL);
    if (szMode == NULL)
    {
        FAIL;
        return FALSE;
    }

    m_pFile = _tfopen (szFileName, szMode);
    return (m_pFile != NULL);
}

INT_P CVDiskFile::read (void* buf, const INT_P npSize)
{
    ASSERT_RW_ADR (buf, npSize);

    if (m_pFile == NULL)
        return 0;

    return fread (buf, 1, npSize, m_pFile);
}

BOOL_P CVDiskFile::write (const void* buf, const INT_P npSize)
{
    ASSERT_R_ADR (buf, npSize);

    if (m_pFile == NULL)
        return FALSE;

    return ((INT_P)fwrite (buf, 1, npSize, m_pFile) == npSize);
}

void CVDiskFile::close ()
{
    if (m_pFile != NULL)
    {
        fclose (m_pFile);
        m_pFile = NULL;
    }
}

BOOL_P CVDiskFile::seek (const INT_P npOffset, const INT_P npOrigin)
{
    ASSERT (npOrigin == SEEK_CUR || npOrigin == SEEK_END || npOrigin == SEEK_SET);

    if (m_pFile == NULL)
        return FALSE;
    else
        return (fseek (m_pFile, (long)npOffset, (int)npOrigin) == 0);
}

INT_P CVDiskFile::tell () const
{
    if (m_pFile == NULL)
        return 0;
    else
        return ftell (m_pFile);
}

BOOL_P CVDiskFile::eof () const
{
    if (m_pFile == NULL)
        return TRUE;
    else
        return (feof (m_pFile) != 0);
}

INT_P CVDiskFile::GetSize () const
{
    if (m_pFile == NULL)
        return 0;

    const INT_P npCurrentPos = ftell (m_pFile);  // 备份当前文件指针位置
    fseek (m_pFile, 0, SEEK_END);  // 将当前文件指针移动到文件尾部
    const INT_P npSize = ftell (m_pFile);  // 记录文件的尺寸
    fseek (m_pFile, (long)npCurrentPos, SEEK_SET);  // 恢复当前文件指针的位置

    return npSize;
}

//----------------------------------------------------------------------

INT_P CVMemoryFile::read (void* buf, const INT_P npSize)
{
    ASSERT_RW_ADR (buf, npSize);

    const INT_P npRemainSize = m_memData.GetSize () - m_npCurrentOffset;
    const INT_P npRealReadSize = (npSize > npRemainSize ? npRemainSize : npSize);

    COPY_MEM (buf, m_memData.GetPtr () + m_npCurrentOffset, npRealReadSize);
    m_npCurrentOffset += npRealReadSize;

    return npRealReadSize;
}

BOOL_P CVMemoryFile::write (const void* buf, const INT_P npSize)
{
    ASSERT_R_ADR (buf, npSize);

    if (npSize > m_memData.GetSize () - m_npCurrentOffset)
        m_memData.Realloc (m_npCurrentOffset + npSize);

    COPY_MEM (m_memData.GetPtr () + m_npCurrentOffset, buf, npSize);
    m_npCurrentOffset += npSize;

    return TRUE;
}

BOOL_P CVMemoryFile::seek (const INT_P npOffset, const INT_P npOrigin)
{
    INT_P npNewOffset = npOffset;
    switch (npOrigin)
    {
    case SEEK_CUR:  npNewOffset += m_npCurrentOffset;  break;
    case SEEK_END:  npNewOffset += m_memData.GetSize ();  break;
    case SEEK_SET:  break;
    default:
        FAIL;
        return FALSE;
    }

    if (npNewOffset < 0 || npNewOffset > m_memData.GetSize ())
        return FALSE;

    m_npCurrentOffset = npNewOffset;
    return TRUE;
}

//----------------------------------------------------------------------

BOOL_P CVFileInputStream::close ()
{
    if (CVBaseInputStream::close () == FALSE)
        return FALSE;

    if (m_pFile != NULL)
    {
        m_pFile->close ();
        m_pFile->Release ();
        m_pFile = NULL;
    }

    return TRUE;
}

BOOL_P CVFileInputStream::OpenFile (const TCHAR* szFileName)
{
    CVDiskFile* pVolFile = new CVDiskFile;

    if (pVolFile->open (szFileName, VFOM_READ) == FALSE)
    {
        pVolFile->Release ();
        return FALSE;
    }

    close ();
    ASSERT (m_pFile == NULL);

    m_pFile = pVolFile;
    return TRUE;
}

//----------------------------------------------------------------------

BOOL_P CVFileOutputStream::close ()
{
    if (CVBaseOutputStream::close () == FALSE)
        return FALSE;

    if (m_pFile != NULL)
    {
        m_pFile->close ();
        m_pFile->Release ();
        m_pFile = NULL;
    }

    return TRUE;
}

BOOL_P CVFileOutputStream::OpenFile (const TCHAR* szFileName, const BOOL_P blpAppend)
{
    CVDiskFile* pVolFile = new CVDiskFile;

    if (pVolFile->open (szFileName, (blpAppend ? VFOM_APPEND : VFOM_WRITE)) == FALSE)
    {
        pVolFile->Release ();
        return FALSE;
    }

    close ();
    ASSERT (m_pFile == NULL);

    m_pFile = pVolFile;
    return TRUE;
}

//----------------------------------------------------------------------

BOOL_P CVMemoryInputStream::close ()
{
    if (CVBaseInputStream::close () == FALSE)
        return FALSE;

    m_memBuf.Free ();
    m_pEnd = m_pCurrent = NULL;
    return TRUE;
}

void CVMemoryInputStream::ResetMemory (const void* pData, const INT_P npDataSize)
{
    ASSERT_R_ADR (pData, npDataSize);

    close ();

    m_memBuf.CopyFrom (pData, npDataSize);
    m_pCurrent = m_memBuf.GetPtr ();
    m_pEnd = m_pCurrent + npDataSize;
}

INT_P CVMemoryInputStream::real_read (void* buf, INT_P npSize)
{
    ASSERT_RW_ADR (buf, npSize);

    if (m_memBuf.IsEmpty ())
        return 0;

    if (npSize > m_pEnd - m_pCurrent)
        npSize = m_pEnd - m_pCurrent;
    COPY_MEM (buf, m_pCurrent, npSize);
    m_pCurrent += npSize;

    return npSize;
}

BOOL_P CVMemoryInputStream::real_skip (const INT_P npSize)
{
    if (npSize > m_pEnd - m_pCurrent)
        return FALSE;

    m_pCurrent += npSize;
    return TRUE;
}

//----------------------------------------------------------------------

BOOL_P CVMemoryOutputStream::close ()
{
    if (CVBaseOutputStream::close () == FALSE)
        return FALSE;

    m_memBuf.Free ();
    return TRUE;
}

const void* CVMemoryOutputStream::GetCurrentData (INT_P* pnpDataSize) const
{
    ASSERT_RW_DATA_OR_NULL (pnpDataSize);

    if (((CVMemoryOutputStream*)this)->flush () == FALSE)
    {
        if (pnpDataSize != NULL)
            *pnpDataSize = 0;
        return NULL;
    }

    if (pnpDataSize != NULL)
        *pnpDataSize = m_memBuf.GetSize ();
    return m_memBuf.GetPtr ();
}

BOOL_P CVMemoryOutputStream::GetCurrentData (CVolMem& memBuf) const
{
    memBuf.Empty ();

    INT_P npDataSize;
    const void* pData = GetCurrentData (&npDataSize);
    if (pData == NULL)
        return FALSE;

    memBuf.CopyFrom (pData, npDataSize);
    return TRUE;
}

const void* CVolMemoryOutputStream::GetCurrentData (INT_P* pnpDataSize) const
{
    if (GetMemoryOutputStream () == NULL)
    {
        if (pnpDataSize != NULL)
            *pnpDataSize = 0;
        return NULL;
    }

    return GetMemoryOutputStream ()->GetCurrentData (pnpDataSize);
}

BOOL_P CVolMemoryOutputStream::GetCurrentData (CVolMem& memBuf) const
{
    if (GetMemoryOutputStream () == NULL)
    {
        memBuf.Free ();
        return FALSE;
    }

    return GetMemoryOutputStream ()->GetCurrentData (memBuf);
}
