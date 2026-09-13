
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_STREAM_H__
#define __VOL_STREAM_H__

// 抛出的异常代码
typedef enum
{
    VESC_NONE           = 0,

    VESC_NULL_STREAM    = -1,
    VESC_UNKNOWN_ERR    = -2,
    VESC_READ_ERR       = -3,
    VESC_WRITE_ERR      = -4,
    VESC_SEEK_ERR       = -5,  // 流当前指针调节或读取错误
    VESC_MEM_ALLOC_ERR  = -6,  // 内存分配错误
    VESC_INVALID_DATA   = -7,  // 无效数据

    _VESC_FORCE_DWORD = _VOL_INT_MAX
}
VOL_STREAM_ERROR_CODE;

// 基本流
class CVBaseStream : public CRefObject
{
    DECLARE_DERIVED_CLASS (CVBaseStream)
     
public:
    inline_ CVBaseStream ()
    {
        m_npErrorCode = (INT_P)VESC_NONE;
    }

    virtual ~CVBaseStream ()
    {
    }

public:
    virtual BOOL_P close ()  // 成功返回真，失败返回假并设置错误状态
    {
        ClearError ();
        return TRUE;
    }

    virtual void OnBeforeDestory () override
    {
        close ();
    }

    //----------------------------------------------  错误状态管理

    // 在流操作发生错误后如果要求重新开始流，必须进行此调用以复位错误状态，以免由于错误状态遗留导致后续流操作被跳过.
    inline_ void ClearError ()
    {
        m_npErrorCode = (INT_P)VESC_NONE;
    }

    // 返回当前的错误代码
    inline_ INT_P GetErrorCode () const
    {
        return m_npErrorCode;
    }

    // 检查自从上次ClearError调用后到现在，中间的流操作是否出现了错误
    inline_ BOOL_P IsFoundError () const
    {
        return m_npErrorCode != (INT_P)VESC_NONE;
    }

    inline_ BOOL_P IsSucceeded () const
    {
        return m_npErrorCode == (INT_P)VESC_NONE;
    }

    // 设置当前错误代码，一旦设置了一个非VESC_NONE的错误代码，后续流操作都将被中止. 
    inline_ void SetErrorCode (const INT_P npCode)
    {
        m_npErrorCode = npCode;
    }

protected:
    INT_P m_npErrorCode;
};

// 火山封装对象类. 本类不能定义实例对象.
class CVolBaseStream : public CVolRefObject
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolBaseStream)

public:
    inline_ CVolBaseStream ()
    {
    }

    inline_ CVBaseStream* GetBaseStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVBaseStream));
        return (CVBaseStream*)m_pRefObject;
    }

    inline_ const CVBaseStream* GetBaseStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVBaseStream));
        return (const CVBaseStream*)m_pRefObject;
    }

public:
    inline_ BOOL_P close ()
    {
        return (GetBaseStream () == NULL ? FALSE : GetBaseStream ()->close ());
    }

    inline_ void ClearError ()
    {
        if (GetBaseStream () != NULL)
            GetBaseStream ()->ClearError ();
    }

    inline_ INT_P GetErrorCode () const
    {
        return (GetBaseStream () == NULL ? (INT_P)VESC_NULL_STREAM : GetBaseStream ()->GetErrorCode ());
    }

    inline_ BOOL_P _NAME_COMPILER_AGREED (IsFoundError) () const
    {
        return (GetBaseStream () == NULL || GetBaseStream ()->IsFoundError ());
    }

    inline_ BOOL_P IsSucceeded () const
    {
        return (GetBaseStream () != NULL && GetBaseStream ()->IsSucceeded ());
    }

    inline_ void SetErrorCode (const INT_P npCode)
    {
        if (GetBaseStream () != NULL)
            GetBaseStream ()->SetErrorCode (npCode);
    }
};

//----------------------------------------------------------------------------------

// 基本输入流
class CVBaseInputStream : public CVBaseStream
{
    DECLARE_DERIVED_CLASS (CVBaseInputStream)

public:
    inline_ CVBaseInputStream (const INT_P npBufSize = 4096)
    {
        m_pBufBegin = NULL;
        _reset (npBufSize);
    }

    virtual ~CVBaseInputStream ()
    {
        _cleanup ();
    }

public:
    // 关闭本输入流,然后以所指定的缓存区尺寸重置本对象.
    inline_ void reset (const INT_P npBufSize)
    {
        _cleanup ();
        _reset (npBufSize);
    }

    inline_ INT_P read (void* buf, const INT_P npSize)  // 返回实际读入的字节数
    {
        return _read (buf, npSize);
    }

    // 将当前流读取指针向前调整指定字节数，nSize必须大于等于0. 成功返回真，失败返回假并设置错误状态. 
    inline_ BOOL_P skip (const INT_P npSize)
    {
        return _skip (npSize);
    }

    BOOL_P eof () const;

    // 返回当前流读取指针相对流首部的偏移位置
    inline_ INT_P GetCurrentPosition () const
    {
        ASSERT (m_npReadedDataSize >= (m_pBufValidDataEnd - m_pBufCurrentData));
        return m_npReadedDataSize - (m_pBufValidDataEnd - m_pBufCurrentData);
    }

    virtual BOOL_P close () override;

public:
    inline_ BOOL_P ReadExact (void* buf, const INT_P npSize)
    {
        if (read (buf, npSize) != npSize)
            SetErrorCode (VESC_READ_ERR);
        return IsSucceeded ();
    }

    // 将从当前流位置到流结尾的所有内容读入并附加到mem中,返回读入的字节数目.
    INT_P ReadToEnd (CVolMem& mem);

protected:
    virtual INT_P real_read (void* buf, INT_P npSize)  { return 0; }
    virtual BOOL_P real_skip (const INT_P npSize)  { return FALSE; }
    virtual BOOL_P real_eof () const  { return TRUE; }

protected:
    void _cleanup ();
    void _reset (const INT_P npBufSize);
    INT_P _read (void* buf, const INT_P npSize);
    BOOL_P _skip (INT_P npSize);

    inline_ INT_P _real_read (void* buf, INT_P npSize)
    {
        const INT_P npReadedDataSize = real_read (buf, npSize);
        m_npReadedDataSize += npReadedDataSize;
        return npReadedDataSize;
    }

private:
    BYTE* m_pBufBegin;
    INT_P m_npBufSize;
    BYTE *m_pBufCurrentData, *m_pBufValidDataEnd;
    INT_P m_npReadedDataSize;  // 记录当前已经读入数据的尺寸
};

// 火山封装对象类. 本类不能定义实例对象.
class _NAME_COMPILER_AGREED (CVolBaseInputStream) : public CVolBaseStream
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolBaseInputStream)

public:
    inline_ CVolBaseInputStream ()
    {
    }

    inline_ CVBaseInputStream* GetInputStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVBaseInputStream));
        return (CVBaseInputStream*)m_pRefObject;
    }

    inline_ const CVBaseInputStream* GetInputStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVBaseInputStream));
        return (const CVBaseInputStream*)m_pRefObject;
    }

public:
    inline_ void reset (const INT_P npBufSize)
    {
        if (GetInputStream () != NULL)
            GetInputStream ()->reset (npBufSize);
    }

    inline_ INT_P read (void* buf, const INT_P npSize)
    {
        return (GetInputStream () == NULL ? 0 : GetInputStream ()->read (buf, npSize));
    }

    inline_ INT_P read (CVolMem& memBuf, INT_P npSize)
    {
        npSize = read (memBuf.Alloc (npSize), npSize);
        memBuf.Realloc (npSize);
        return npSize;
    }

    inline_ BOOL_P skip (const INT_P npSize)
    {
        return (GetInputStream () == NULL ? FALSE : GetInputStream ()->skip (npSize));
    }

    inline_ BOOL_P eof () const
    {
        return (GetInputStream () == NULL ? TRUE : GetInputStream ()->eof ());
    }

    inline_ INT_P GetCurrentPosition () const
    {
        return (GetInputStream () == NULL ? 0 : GetInputStream ()->GetCurrentPosition ());
    }

    inline_ INT_P ReadToEnd (CVolMem& mem)
    {
        mem.Empty ();
        return (GetInputStream () == NULL ? 0 : GetInputStream ()->ReadToEnd (mem));
    }

    inline_ BOOL_P _NAME_COMPILER_AGREED (ReadExact) (void* buf, const INT_P npSize)
    {
        return (GetInputStream () == NULL ? FALSE : GetInputStream ()->ReadExact (buf, npSize));
    }

    inline_ BOOL_P ReadExact (CVolMem& memBuf, INT_P npSize)
    {
        return ReadExact (memBuf.Alloc (npSize), npSize);
    }

    #define _STRAEM_LOAD_BASE_DATA(data_type)  \
        inline_ CVolBaseInputStream& LoadValue_##data_type (data_type& value)  \
        {  \
            ReadExact (&value, sizeof (value));  \
            return *this;  \
        }

    _STRAEM_LOAD_BASE_DATA (S_BYTE)
    _STRAEM_LOAD_BASE_DATA (SHORT)
    _STRAEM_LOAD_BASE_DATA (TCHAR)
    _STRAEM_LOAD_BASE_DATA (INT)
    _STRAEM_LOAD_BASE_DATA (INT64)
    _STRAEM_LOAD_BASE_DATA (DOUBLE)
    _STRAEM_LOAD_BASE_DATA (FLOAT)
    _STRAEM_LOAD_BASE_DATA (BOOL)

    inline_ CVolBaseInputStream& LoadValue_CVolString (CVolString& str)
    {
        return str.VolLoadFromStream (*this);
    }

    inline_ CVolBaseInputStream& operator>> (S_BYTE& sb)
    {
        ReadExact (&sb, sizeof (sb));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (BYTE& bt)
    {
        ReadExact (&bt, sizeof (bt));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (SHORT& sht)
    {
        ReadExact (&sht, sizeof (sht));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (WORD& w)
    {
        ReadExact (&w, sizeof (w));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (INT& n)
    {
        ReadExact (&n, sizeof (n));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (DWORD& dw)
    {
        ReadExact (&dw, sizeof (dw));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (INT64& n64)
    {
        ReadExact (&n64, sizeof (n64));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (UINT64& u64)
    {
        ReadExact (&u64, sizeof (u64));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (FLOAT& flt)
    {
        ReadExact (&flt, sizeof (flt));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (DOUBLE& db)
    {
        ReadExact (&db, sizeof (db));
        return *this;
    }

    inline_ CVolBaseInputStream& operator>> (TCHAR& ch)
    {
        ReadExact (&ch, sizeof (ch));
        return *this;
    }
};

//----------------------------------------------------------------------------------

// 基本输出流
class CVBaseOutputStream : public CVBaseStream
{
    DECLARE_DERIVED_CLASS (CVBaseOutputStream)

public:
    inline_ CVBaseOutputStream (const INT_P npBufSize = 4096)
    {
        m_pBufBegin = NULL;
        _reset (npBufSize);
    }

    virtual ~CVBaseOutputStream ()
    {
        _cleanup ();
    }

public:
    // 关闭本输出流,然后以所指定的缓存区尺寸重置本对象.
    inline_ void reset (const INT_P npBufSize)
    {
        _cleanup ();
        _reset (npBufSize);
    }

    virtual BOOL_P flush ();  // 成功返回真，失败返回假并设置错误状态
    virtual BOOL_P close () override;

    //-------------------------------------------

    // 成功返回真，失败返回假并设置错误状态
    inline_ BOOL_P write (const void* pBuf, const INT_P npSize)
    {
        return _write (pBuf, npSize);
    }

protected:
    void _cleanup ();
    void _reset (const INT_P npBufSize);
    BOOL_P _write (const void* pBuf, const INT_P npSize);
    virtual BOOL_P real_write (const void* buf, const INT_P npSize)  { return FALSE; }

private:
    BYTE *m_pBufBegin, *m_pBufEnd, *m_pBufCurrent;
};

// 火山封装对象类. 本类不能定义实例对象.
class _NAME_COMPILER_AGREED (CVolBaseOutputStream) : public CVolBaseStream
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolBaseOutputStream)

public:
    inline_ CVolBaseOutputStream ()
    {
    }

    inline_ CVBaseOutputStream* GetOutputStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVBaseOutputStream));
        return (CVBaseOutputStream*)m_pRefObject;
    }

    inline_ const CVBaseOutputStream* GetOutputStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVBaseOutputStream));
        return (const CVBaseOutputStream*)m_pRefObject;
    }

public:
    inline_ void reset (const INT_P npBufSize)
    {
        if (GetOutputStream () != NULL)
            GetOutputStream ()->reset (npBufSize);
    }

    inline_ BOOL_P flush ()
    {
        return (GetOutputStream () == NULL ? FALSE : GetOutputStream ()->flush ());
    }

    inline_ BOOL_P _NAME_COMPILER_AGREED (write) (const void* pBuf, const INT_P npSize)
    {
        return (GetOutputStream () == NULL ? FALSE : GetOutputStream ()->write (pBuf, npSize));
    }

    inline_ BOOL_P write (const CVolMem& mem)
    {
        return write (mem.GetPtr (), mem.GetSize ());
    }

    #define _STRAEM_SAVE_BASE_DATA(data_type)  \
        inline_ CVolBaseOutputStream& SaveValue_##data_type (const data_type value)  \
        {  \
            write (&value, sizeof (value));  \
            return *this;  \
        }

    _STRAEM_SAVE_BASE_DATA (S_BYTE)
    _STRAEM_SAVE_BASE_DATA (SHORT)
    _STRAEM_SAVE_BASE_DATA (TCHAR)
    _STRAEM_SAVE_BASE_DATA (INT)
    _STRAEM_SAVE_BASE_DATA (INT64)
    _STRAEM_SAVE_BASE_DATA (DOUBLE)
    _STRAEM_SAVE_BASE_DATA (FLOAT)
    _STRAEM_SAVE_BASE_DATA (BOOL)

    inline_ CVolBaseOutputStream& SaveValue_CVolString (const CVolString& str)
    {
        return str.VolSaveIntoStream (*this);
    }

    inline_ CVolBaseOutputStream& operator<< (const S_BYTE sb)
    {
        write (&sb, sizeof (sb));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const BYTE bt)
    {
        write (&bt, sizeof (bt));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const SHORT sht)
    {
        write (&sht, sizeof (sht));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const WORD w)
    {
        write (&w, sizeof (w));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const INT n)
    {
        write (&n, sizeof (n));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const INT64 n64)
    {
        write (&n64, sizeof (n64));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const UINT64 u64)
    {
        write (&u64, sizeof (u64));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const DWORD dw)
    {
        write (&dw, sizeof (dw));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const FLOAT flt)
    {
        write (&flt, sizeof (flt));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const DOUBLE db)
    {
        write (&db, sizeof (db));
        return *this;
    }

    inline_ CVolBaseOutputStream& operator<< (const TCHAR ch)
    {
        write (&ch, sizeof (ch));
        return *this;
    }
};

//----------------------------------------------------------------------------------

// 基本文件
class CVBaseFile : public CRefObject
{
    DECLARE_DERIVED_CLASS (CVBaseFile)

public:
    inline_ CVBaseFile ()
    {
    }

    virtual ~CVBaseFile ()
    {
    }

public:
    virtual INT_P read (void* buf, const INT_P npSize)  { return 0; }  // 读入nSize尺寸的数据到buf缓冲区,返回所实际读入数据的尺寸.
    virtual BOOL_P write (const void* buf, const INT_P npSize)  { return FALSE; }  // 写入buf缓冲区中尺寸为nSize的数据,成功返回真,失败返回假.
    virtual void close ()  { }  // 关闭本文件

    // nOrigin为以下值之一: SEEK_CUR:从当前文件指针处开始; SEEK_END:从文件尾开始; SEEK_SET:从文件首开始.
    virtual BOOL_P seek (const INT_P npOffset, const INT_P npOrigin)  { return FALSE; }  // 重定位文件读写指针到nOffset处,成功返回真,失败返回假.
    virtual INT_P tell () const  { return 0; }  // 返回当前文件读写指针的位置
    virtual BOOL_P eof () const  { return TRUE; }  // 返回当前文件读写指针是否位于文件末尾
    virtual INT_P GetSize () const  { return 0; }  // 返回文件尺寸

    inline_ BOOL_P seek (const INT_P npOffset)
    {
        return seek (npOffset, SEEK_SET);
    }

    inline_ BOOL_P skip (const INT_P npSize)
    {
        return seek (npSize, SEEK_CUR);
    }

    INT_P ReadToEnd (CVolMem& mem);  // 将从当前文件指针到结尾的所有内容读入并附加到mem中,返回读入的字节数目.
};

//----------------------------------------------------------------------------------

typedef enum
{
    VFOM_READ,   // 打开读,要求文件必须存在
    VFOM_WRITE,  // 打开写,如果文件存在则先清除原有内容,如果文件不存在则自动建立.
    VFOM_APPEND,  // 打开附加,如果文件存在则在其尾部写出,如果文件不存在则自动建立.
}
VOL_FILE_OPEN_MODE;

// 磁盘文件
class CVDiskFile : public CVBaseFile
{
    DECLARE_DERIVED_CLASS (CVDiskFile)

public:
    inline_ CVDiskFile ()
    {
        m_pFile = NULL;
    }

    virtual ~CVDiskFile ()
    {
        close ();
    }

public:
    virtual INT_P read (void* buf, const INT_P npSize) override;
    virtual BOOL_P write (const void* buf, const INT_P npSize) override;
    virtual void close () override;

    virtual BOOL_P seek (const INT_P npOffset, const INT_P npOrigin) override;
    virtual INT_P tell () const override;
    virtual BOOL_P eof () const override;
    virtual INT_P GetSize () const override;

public:  // 自身增加的接口
    virtual BOOL_P open (const TCHAR* szFileName, const VOL_FILE_OPEN_MODE enOpenMode);

protected:
    FILE* m_pFile;
};

//----------------------------------------------------------------------------------

// 内存文件
class CVMemoryFile : public CVBaseFile
{
    DECLARE_DERIVED_CLASS (CVMemoryFile)

public:
    inline_ CVMemoryFile ()
    {
        m_npCurrentOffset = 0;
    }

    inline_ CVMemoryFile (const void* pData, const INT_P npDataSize)
    {
        init (pData, npDataSize);
    }

public:
    inline_ void init (const void* pData, const INT_P npDataSize)
    {
        m_memData.CopyFrom (pData, npDataSize);
        m_npCurrentOffset = 0;
    }

    virtual INT_P read (void* buf, const INT_P npSize) override;
    virtual BOOL_P write (const void* buf, const INT_P npSize) override;

    virtual void close () override
    {
        m_memData.Free ();
        m_npCurrentOffset = 0;
    }

    virtual BOOL_P seek (const INT_P npOffset, const INT_P npOrigin) override;

    virtual INT_P tell () const override
    {
        return m_npCurrentOffset;
    }

    virtual BOOL_P eof () const override
    {
        return (m_npCurrentOffset >= m_memData.GetSize ());
    }

    virtual INT_P GetSize () const override
    {
        return GetDataSize ();
    }

    inline_ const BYTE* GetData () const
    {
        return m_memData.GetPtr ();
    }

    inline_ INT_P GetDataSize () const
    {
        return m_memData.GetSize ();
    }

protected:
    CVolMem m_memData;
    INT_P m_npCurrentOffset;
};

//----------------------------------------------------------------------------------

// 文件输入流
class CVFileInputStream : public CVBaseInputStream
{
    DECLARE_DERIVED_CLASS (CVFileInputStream)

public:
    inline_ CVFileInputStream (const INT_P npBufSize = 4096) :
            CVBaseInputStream (npBufSize)
    {
        m_pFile = NULL;
    }

    virtual ~CVFileInputStream ()
    {
        close ();
    }

    virtual BOOL_P close () override;

    // 打开所指定文件,返回是否成功.
    BOOL_P OpenFile (const TCHAR* szFileName);

protected:
    virtual INT_P real_read (void* buf, INT_P npSize) override
    {
        return (m_pFile != NULL ? m_pFile->read (buf, npSize) : 0);
    }

    virtual BOOL_P real_skip (const INT_P npSize) override
    {
        return (m_pFile != NULL ? m_pFile->skip (npSize) : FALSE);
    }

    virtual BOOL_P real_eof () const override
    {
        return (m_pFile != NULL ? m_pFile->eof () : TRUE);
    }

private:
    CVBaseFile* m_pFile;
};

// 火山封装对象类
class CVolFileInputStream : public CVolBaseInputStream
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolFileInputStream)

public:
    inline_ CVolFileInputStream ()
    {
        ASSERT (m_pRefObject == NULL);
        m_pRefObject = new CVFileInputStream;
    }

    inline_ CVFileInputStream* GetFileInputStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVFileInputStream));
        return (CVFileInputStream*)m_pRefObject;
    }

    inline_ const CVFileInputStream* GetFileInputStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVFileInputStream));
        return (const CVFileInputStream*)m_pRefObject;
    }

public:
    inline_ BOOL_P OpenFile (const TCHAR* szFileName)
    {
        return (GetFileInputStream () == NULL ? FALSE : GetFileInputStream ()->OpenFile (szFileName));
    }
};

//----------------------------------------------------------------------------------

// 文件输出流
class CVFileOutputStream : public CVBaseOutputStream
{
    DECLARE_DERIVED_CLASS (CVFileOutputStream)

public:
    inline_ CVFileOutputStream (const INT_P npBufSize = 4096) :
            CVBaseOutputStream (npBufSize)
    {
        m_pFile = NULL;
    }

    virtual ~CVFileOutputStream ()
    {
        close ();
    }

    virtual BOOL_P close () override;

    // 打开所指定文件,返回是否成功.
    BOOL_P OpenFile (const TCHAR* szFileName, const BOOL_P blpAppend);

protected:
    virtual BOOL_P real_write (const void* buf, const INT_P npSize)
    {
        return (m_pFile != NULL ? m_pFile->write (buf, npSize) : FALSE);
    }

private:
    CVBaseFile* m_pFile;
};

// 火山封装对象类
class CVolFileOutputStream : public CVolBaseOutputStream
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolFileOutputStream)

public:
    inline_ CVolFileOutputStream ()
    {
        ASSERT (m_pRefObject == NULL);
        m_pRefObject = new CVFileOutputStream;
    }

    inline_ CVFileOutputStream* GetFileOutputStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVFileOutputStream));
        return (CVFileOutputStream*)m_pRefObject;
    }

    inline_ const CVFileOutputStream* GetFileOutputStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVFileOutputStream));
        return (const CVFileOutputStream*)m_pRefObject;
    }

public:
    inline_ BOOL_P OpenFile (const TCHAR* szFileName, const BOOL_P blpAppend)
    {
        return (GetFileOutputStream () == NULL ? FALSE : GetFileOutputStream ()->OpenFile (szFileName, blpAppend));
    }
};

//----------------------------------------------------------------------------------

// 内存输入流
class CVMemoryInputStream : public CVBaseInputStream
{
    DECLARE_DERIVED_CLASS (CVMemoryInputStream)

public:
    inline_ CVMemoryInputStream () : CVBaseInputStream (0)
    {
        m_pEnd = m_pCurrent = NULL;
    }

    virtual ~CVMemoryInputStream ()
    {
        close ();
    }

    // 重新设置内存流的来源数据
    void ResetMemory (const void* pData, const INT_P npDataSize);

    inline_ void ResetMemory (const CVolMem& mem)
    {
        ResetMemory (mem.GetPtr (), mem.GetSize ());
    }

    virtual BOOL_P close () override;

protected:
    virtual INT_P real_read (void* buf, INT_P npSize) override;
    virtual BOOL_P real_skip (const INT_P npSize) override;

    virtual BOOL_P real_eof () const override
    {
        return (m_pCurrent >= m_pEnd);
    }

private:
    const BYTE *m_pEnd, *m_pCurrent;
    CVolMem m_memBuf;
};

// 火山封装对象类
class CVolMemoryInputStream : public CVolBaseInputStream
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolMemoryInputStream)

public:
    inline_ CVolMemoryInputStream ()
    {
        ASSERT (m_pRefObject == NULL);
        m_pRefObject = new CVMemoryInputStream;
    }

    inline_ CVMemoryInputStream* GetMemoryInputStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVMemoryInputStream));
        return (CVMemoryInputStream*)m_pRefObject;
    }

    inline_ const CVMemoryInputStream* GetMemoryInputStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVMemoryInputStream));
        return (const CVMemoryInputStream*)m_pRefObject;
    }

public:
    inline_ void ResetMemory (const void* pData, const INT_P npDataSize)
    {
        if (GetMemoryInputStream () != NULL)
            GetMemoryInputStream ()->ResetMemory (pData, npDataSize);
    }

    inline_ void ResetMemory (const CVolMem& mem)
    {
        if (GetMemoryInputStream () != NULL)
            GetMemoryInputStream ()->ResetMemory (mem);
    }
};

//----------------------------------------------------------------------------------

// 内存输出流
class CVMemoryOutputStream : public CVBaseOutputStream
{
    DECLARE_DERIVED_CLASS (CVMemoryOutputStream)

public:
    inline_ CVMemoryOutputStream () : CVBaseOutputStream (0)
    {
    }

    virtual ~CVMemoryOutputStream ()
    {
        close ();
    }

public:
    virtual BOOL_P close () override;

    // 设置分配内存时的对齐尺寸,避免频繁重分配内存.
    // 如果小于等于0,则默认为_DEFAULT_MEM_ALIGN_SIZE.
    inline_ void SetMemAlignSize (const INT_P npAlignSize)
    {
        m_memBuf.SetMemAlignSize (npAlignSize);
    }

    // 获得流中的当前数据,失败返回NULL.
    const void* GetCurrentData (INT_P* pnpDataSize) const;

    inline_ CVolMem& GetBin ()
    {
        flush ();
        return m_memBuf;
    }

    // 获得流中的当前数据,返回是否成功.
    BOOL_P GetCurrentData (CVolMem& memBuf) const;

    // 清除流中的当前所有数据
    inline_ void Empty ()
    {
        ((CVMemoryOutputStream*)this)->flush ();
        m_memBuf.Empty ();
    }

protected:
    virtual BOOL_P real_write (const void* buf, const INT_P npSize)
    {
        m_memBuf.Append (buf, npSize);
        return TRUE;
    }

private:
    CVolMem m_memBuf;
};

// 火山封装对象类
class CVolMemoryOutputStream : public CVolBaseOutputStream
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolMemoryOutputStream)

public:
    inline_ CVolMemoryOutputStream ()
    {
        ASSERT (m_pRefObject == NULL);
        m_pRefObject = new CVMemoryOutputStream;
    }

    inline_ CVMemoryOutputStream* GetMemoryOutputStream ()
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVMemoryOutputStream));
        return (CVMemoryOutputStream*)m_pRefObject;
    }

    inline_ const CVMemoryOutputStream* GetMemoryOutputStream () const
    {
        ASSERT (m_pRefObject == NULL || P_IS_INSTANCE_OF (m_pRefObject, CVMemoryOutputStream));
        return (const CVMemoryOutputStream*)m_pRefObject;
    }

public:
    inline_ void SetMemAlignSize (const INT_P npAlignSize)
    {
        ASSERT (GetMemoryOutputStream () != NULL);
        GetMemoryOutputStream ()->SetMemAlignSize (npAlignSize);
    }

    inline_ void Empty ()
    {
        ASSERT (GetMemoryOutputStream () != NULL);
        GetMemoryOutputStream ()->Empty ();
    }

    const void* GetCurrentData (INT_P* pnpDataSize) const;
    BOOL_P GetCurrentData (CVolMem& memBuf) const;

    inline_ CVolMem& GetBin (CVolMem& memEmpty)
    {
        ASSERT (memEmpty.IsEmpty ());
        return (GetMemoryOutputStream () == NULL ? memEmpty : GetMemoryOutputStream ()->GetBin ());
    }
};

#endif
