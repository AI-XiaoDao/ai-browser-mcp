
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_MEM_H__
#define __VOL_MEM_H__

// 默认内存分配时的对齐尺寸
#define _DEFAULT_MEM_ALIGN_SIZE  64

//----------------------------------------------------------------------------

class CVolString;
class CVolBaseInputStream;
class CVolBaseOutputStream;
class CVolObjectArray;

// 内存管理类
class _NAME_COMPILER_AGREED (CVolMem) : public CVolObject
{
    DECLARE_GLOBAL_VOL_CLASS_NOT_OVR_COMP (CVolMem)

public:
    CVolMem ();

    #define _BASE_DATA_CONSTRUCT(data_type)   \
            inline_ CVolMem (data_type data) : CVolMem ()  \
            {                                        \
                Append (&data, sizeof (data_type));   \
            }

    _BASE_DATA_CONSTRUCT (S_BYTE)
    _BASE_DATA_CONSTRUCT (SHORT)
    _BASE_DATA_CONSTRUCT (TCHAR)
    _BASE_DATA_CONSTRUCT (INT)
    _BASE_DATA_CONSTRUCT (INT64)
    _BASE_DATA_CONSTRUCT (FLOAT)
    _BASE_DATA_CONSTRUCT (DOUBLE)

    inline_ CVolMem (const void* pData, const INT_P npSize) : CVolMem ()
    {
        Append (pData, npSize);
    }

    CVolMem (const CVolString& str);

    virtual ~CVolMem ()
    {
        Free ();
    }

public:
    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override;
    virtual void LoadFromStream (CVolBaseInputStream& stream) override;
    virtual void SaveIntoStream (CVolBaseOutputStream& stream) override;

    inline_ friend CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, CVolMem& mem)
    {
        mem.LoadFromStream (stream);
        return stream;
    }

    inline_ friend CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const CVolMem& mem)
    {
        return mem.VolSaveIntoStream (stream);
    }

    inline_ const BYTE* GetPtr () const
    {
        return (m_npSize == 0 ? NULL : m_pData);
    }

    inline_ BYTE* GetPtr ()
    {
        return (m_npSize == 0 ? NULL : m_pData);
    }

    // 返回尾指针
    inline_ const BYTE* GetEndPtr () const
    {
        return (m_npSize == 0 ? NULL : m_pData + m_npSize);
    }

    inline_ INT_P GetSize () const
    {
        return m_npSize;
    }

    inline_ DWORD GetHash () const
    {
        return GetBinHash (m_pData, m_npSize);
    }

    inline_ BOOL_P IsEmpty () const
    {
        return (m_npSize == 0);
    }

    inline_ CVolMem GetBinLeft (const INT_P npSize) const
    {
        ASSERT (npSize >= 0);
        return CVolMem (m_pData, MIN (npSize, m_npSize));
    }

    inline_ CVolMem GetBinRight (INT_P npSize) const
    {
        ASSERT (npSize >= 0);
        if (npSize > m_npSize)
            npSize = m_npSize;
        return CVolMem (m_pData + m_npSize - npSize, npSize);
    }

    CVolMem GetBinMid (INT_P npOffset, INT_P npSize) const;

    // 返回指定指针是否处在本内存对象的尾部
    inline_ BOOL_P IsAtEnd (const void* pData) const
    {
        if (m_npSize == 0)
            return (pData == NULL);
        else
            return ((const BYTE*)pData == m_pData + m_npSize);
    }

    // 返回指定数据段是否在本内存对象内
    inline_ BOOL_P IsInside (const void* pData, const INT_P npDataSize) const
    {
        ASSERT (pData != NULL && npDataSize >= 0);

        if (m_npSize == 0)
            return FALSE;

        return ((const BYTE*)pData >= m_pData && (const BYTE*)pData + npDataSize <= m_pData + m_npSize);
    }

    // 返回指定偏移数据段是否在本内存对象内
    inline_ BOOL_P IsOffsetInside (const INT_P npDataOffset, const INT_P npDataSize) const
    {
        ASSERT (npDataSize >= 0);

        return (npDataOffset >= 0 && npDataOffset + npDataSize <= m_npSize);
    }

    inline_ BOOL_P IsEqual (const void* pData, const INT_P npDataSize) const
    {
        ASSERT_R_ADR (pData, npDataSize);
        return (m_npSize == npDataSize && memcmp (m_pData, pData, npDataSize) == 0);
    }

    inline_ BOOL_P IsEqual (const CVolMem* pMem) const
    {
        ASSERT_RW_DATA (pMem);
        return (m_npSize == pMem->m_npSize && memcmp (m_pData, pMem->m_pData, m_npSize) == 0);
    }

    //----------------------------------------------------------------------

    // 设置分配内存时的对齐尺寸,避免频繁重分配内存.
    // 如果小于等于0,则默认为_DEFAULT_MEM_ALIGN_SIZE.
    inline_ void SetMemAlignSize (const INT_P npAlignSize)
    {
        ASSERT (npAlignSize >= 0);
        m_npMemAlignSize = npAlignSize;
    }
    inline_ INT_P GetMemAlignSize () const
    {
        return m_npMemAlignSize;
    }

    BYTE* Alloc (const INT_P npSize);
    BYTE* Realloc (const INT_P npSize);
    void Free ();

    inline_ BYTE* Alloc (const INT_P npSize, const BOOL_P blpZero)
    {
        BYTE* pb = Alloc (npSize);
        if (blpZero)
            Zero ();
        return pb;
    }

    void* AddSpace (const INT_P npSize, const BOOL_P blpZero);  // 添加指定尺寸的空间,返回该空间的首地址.
    void* InsertSpace (const INT_P npOffset, const INT_P npSize, const BOOL_P blpZero);  // 插入指定尺寸的空间,返回该空间的首地址.

    inline_ void Zero ()
    {
        ZERO_MEM (m_pData, m_npSize);
    }

    // 清空本对象但是不实际释放内存以备下一次分配
    inline_ void Empty ()
    {
        m_npSize = 0;
    }

    inline_ void CopyFrom (const void* pData, const INT_P npSize)
    {
        Empty ();
        Append (pData, npSize);
    }

    // 在指定偏移位置处插入指定尺寸的数据
    //   pData: 如果为NULL,则插入空白数据.
    void Insert (const INT_P npOffset, const void* pData, const INT_P npSize);

    inline_ void Insert (const INT_P npOffset, const CVolMem& mem)
    {
        Insert (npOffset, mem.GetPtr (), mem.GetSize ());
    }

    inline_ void InsertInt (const INT_P npOffset, const INT nValue)
    {
        Insert (npOffset, &nValue, sizeof (INT));
    }

    inline_ void InsertChar (const INT_P npOffset, TCHAR ch)
    {
        Insert (npOffset, &ch, sizeof (TCHAR));
    }

    inline_ void InsertOnlyText (const INT_P npOffset, const WCHAR* pws, const INT_P npLen)
    {
        Insert (npOffset, pws, npLen * (INT_P)sizeof (WCHAR));
    }
    inline_ void InsertOnlyText (const INT_P npOffset, const U8CHAR* ps, const INT_P npLen)
    {
        Insert (npOffset, ps, npLen * (INT_P)sizeof (U8CHAR));
    }

    inline_ void InsertOnlyText (const INT_P npOffset, const WCHAR* pws)
    {
        ASSERT_R_STR (pws);
        InsertOnlyText (npOffset, pws, wcslen (pws));
    }
    inline_ void InsertOnlyText (const INT_P npOffset, const U8CHAR* ps)
    {
        ASSERT_R_STR (ps);
        InsertOnlyText (npOffset, ps, strlen (ps));
    }

    inline_ void InsertString (const INT_P npOffset, const WCHAR* pws)
    {
        ASSERT_R_STR (pws);
        InsertOnlyText (npOffset, pws, wcslen (pws) + 1);
    }
    inline_ void InsertString (const INT_P npOffset, const U8CHAR* ps)
    {
        ASSERT_R_STR (ps);
        InsertOnlyText (npOffset, ps, strlen (ps) + 1);
    }

    inline_ void Append (const CVolMem& mem)
    {
        Append (mem.GetPtr (), mem.GetSize ());
    }

    void Append (const void* pData, const INT_P npSize);
    void Replace (const INT_P npOffset, INT_P npSize, const void* pReplaceData, const INT_P npReplaceSize);

    inline_ void Replace (const INT_P npOffset, const INT_P npSize, const CVolMem& binReplace)
    {
        Replace (npOffset, npSize, binReplace.GetPtr (), binReplace.GetSize ());
    }

    // 如果npOffset为-1,则从尾部开始向前删除.
    void Remove (const INT_P npOffset, const INT_P npSize);

    inline_ void RemoveToEnd (const INT_P npOffset)
    {
        ASSERT (npOffset >= 0 && npOffset <= m_npSize);
        Realloc (npOffset);
    }

    // 返回尾部的字符
    inline_ TCHAR GetEndChar () const
    {
        ASSERT (m_npSize >= (INT_P)sizeof (TCHAR));
        return *(TCHAR*)(m_pData + m_npSize - sizeof (TCHAR));
    }
    inline_ WCHAR GetEndWChar () const
    {
        ASSERT (m_npSize >= (INT_P)sizeof (WCHAR));
        return *(WCHAR*)(m_pData + m_npSize - sizeof (WCHAR));
    }
    inline_ U8CHAR GetEndU8Char () const
    {
        ASSERT (m_npSize >= (INT_P)sizeof (U8CHAR));
        return *(U8CHAR*)(m_pData + m_npSize - sizeof (U8CHAR));
    }

    // 返回尾部是否为所指定的字符
    inline_ BOOL_P EndCharOf (const TCHAR ch) const
    {
        return (m_npSize >= (INT_P)sizeof (TCHAR) && GetEndChar () == ch);
    }
    inline_ BOOL_P EndWCharOf (const WCHAR ch) const
    {
        return (m_npSize >= (INT_P)sizeof (WCHAR) && GetEndWChar () == ch);
    }
    inline_ BOOL_P EndU8CharOf (const U8CHAR ch) const
    {
        return (m_npSize >= (INT_P)sizeof (U8CHAR) && GetEndU8Char () == ch);
    }

    // 如果尾部为'\0'字符,则将其删除.
    inline_ void RemoveEndZeroChar ()
    {
        if (EndCharOf ('\0'))
            m_npSize -= (INT_P)sizeof (TCHAR);
    }
    inline_ void RemoveEndZeroWChar ()
    {
        if (EndWCharOf ('\0'))
            m_npSize -= (INT_P)sizeof (WCHAR);
    }
    inline_ void RemoveEndZeroU8Char ()
    {
        if (EndU8CharOf ('\0'))
            m_npSize -= (INT_P)sizeof (U8CHAR);
    }

    //----------------------------------------------------------------------

    #define _BASE_DATA_ADDING(MethodName,data_type)   \
            inline_ void MethodName (data_type data)  \
            {                                        \
                Append (&data, sizeof (data_type));   \
            }

    _BASE_DATA_ADDING (AddByte,    BYTE)
    _BASE_DATA_ADDING (AddChar,    TCHAR)
    _BASE_DATA_ADDING (AddWChar,   WCHAR)
    _BASE_DATA_ADDING (AddU8Char,  U8CHAR)
    _BASE_DATA_ADDING (AddWord,    WORD)
    _BASE_DATA_ADDING (AddDWord,   DWORD)
    _BASE_DATA_ADDING (AddInt,     INT)
    _BASE_DATA_ADDING (AddIntP,    INT_P)
    _BASE_DATA_ADDING (AddUIntP,   UINT_P)
    _BASE_DATA_ADDING (AddInt64,   INT64)
    _BASE_DATA_ADDING (AddUInt64,  UINT64)
    _BASE_DATA_ADDING (AddBool,    BOOL)
    _BASE_DATA_ADDING (AddBoolP,   BOOL_P)
    _BASE_DATA_ADDING (AddFloat,   FLOAT)
    _BASE_DATA_ADDING (AddDouble,  DOUBLE)
    _BASE_DATA_ADDING (AddPointer, void*)
    _BASE_DATA_ADDING (AddPointer, VOID_CPTR)

    void AddManyChars (const TCHAR ch, const INT_P npCount);
    void AddManyWChars (const WCHAR ch, const INT_P npCount);
    void AddManyU8Chars (const U8CHAR ch, const INT_P npCount);
    CVolMem& AddManyBytes (const INT_P npNumBytes, ...);
    void AddString (const WCHAR* pws);
    void AddString (const U8CHAR* ps);
    void AddOnlyText (const WCHAR* pws);
    void AddOnlyText (const U8CHAR* ps);

    inline_ void AddOnlyText (const WCHAR* pws, const INT_P npLen)
    {
        ASSERT (npLen >= 0);
        Append (pws, npLen * sizeof (WCHAR));
    }
    inline_ void AddOnlyText (const U8CHAR* ps, const INT_P npLen)
    {
        ASSERT (npLen >= 0);
        Append (ps, npLen * sizeof (U8CHAR));
    }

    // 将所指定的数据连续加入npNumAddCopies份到本对象中
    // 如果pData为NULL,则加入对应长度的0数据.
    void AddManyCopies (const void* pData, const INT_P npDataSize, const INT_P npNumAddCopies);
    template<typename T> inline_ void TAddManyCopies (const T data, const INT_P npNumAddCopies)
    {
        AddManyCopies (&data, sizeof (T), npNumAddCopies);
    }
    inline_ void AddManyCopies (const CVolMem& mem, const INT_P npNumAddCopies)
    {
        AddManyCopies (mem.GetPtr (), mem.GetSize (), npNumAddCopies);
    }
    inline_ void SetManyCopies (const CVolMem& mem, const INT_P npNumAddCopies)
    {
        Empty ();
        AddManyCopies (mem.GetPtr (), mem.GetSize (), npNumAddCopies);
    }

    inline_ INT_P GetDoubleCount () const        {  return m_npSize / sizeof (DOUBLE);       }
    inline_ INT_P GetFloatCount () const         {  return m_npSize / sizeof (FLOAT);        }
    inline_ INT_P GetDWordCount () const         {  return m_npSize / sizeof (DWORD);        }
    inline_ INT_P GetPointerCount () const       {  return m_npSize / sizeof (const void*);  }
    inline_ INT_P GetWordCount () const          {  return m_npSize / sizeof (WORD);         }
    inline_ INT_P GetIntCount () const           {  return m_npSize / sizeof (INT);          }
    inline_ INT_P GetIntPCount () const          {  return m_npSize / sizeof (INT_P);        }
    inline_ INT_P GetUIntPCount () const         {  return m_npSize / sizeof (UINT_P);       }
    inline_ INT_P GetInt64Count () const         {  return m_npSize / sizeof (INT64);        }
    inline_ INT_P GetUInt64Count () const        {  return m_npSize / sizeof (UINT64);       }
    inline_ INT_P GetBoolCount () const          {  return m_npSize / sizeof (BOOL);         }
    inline_ INT_P GetBoolPCount () const         {  return m_npSize / sizeof (BOOL_P);       }
    inline_ INT_P GetCharCount () const          {  return m_npSize / sizeof (TCHAR);        }

    inline_ const DOUBLE* GetDoublePtr () const  {  return m_npSize < (INT_P)sizeof (DOUBLE) ? NULL : (const DOUBLE*)m_pData;  }
    inline_ const FLOAT* GetFloatPtr () const    {  return m_npSize < (INT_P)sizeof (FLOAT) ? NULL : (const FLOAT*)m_pData;   }
    inline_ const DWORD* GetDWordPtr () const    {  return m_npSize < (INT_P)sizeof (DWORD) ? NULL : (const DWORD*)m_pData;   }
    inline_ const WORD* GetWordPtr () const      {  return m_npSize < (INT_P)sizeof (WORD) ? NULL : (const WORD*)m_pData;    }
    inline_ const INT* GetIntPtr () const        {  return m_npSize < (INT_P)sizeof (INT) ? NULL : (const INT*)m_pData;     }
    inline_ const INT_P* GetIntPPtr () const     {  return m_npSize < (INT_P)sizeof (INT_P) ? NULL : (const INT_P*)m_pData;   }
    inline_ const UINT_P* GetUIntPPtr () const   {  return m_npSize < (INT_P)sizeof (UINT_P) ? NULL : (const UINT_P*)m_pData;  }
    inline_ const INT64* GetInt64Ptr () const    {  return m_npSize < (INT_P)sizeof (INT64) ? NULL : (const INT64*)m_pData;   }
    inline_ const UINT64* GetUInt64Ptr () const  {  return m_npSize < (INT_P)sizeof (UINT64) ? NULL : (const UINT64*)m_pData;  }
    inline_ const BOOL* GetBoolPtr () const      {  return m_npSize < (INT_P)sizeof (BOOL) ? NULL : (const BOOL*)m_pData;    }
    inline_ const BOOL_P* GetBoolPPtr () const   {  return m_npSize < (INT_P)sizeof (BOOL_P) ? NULL : (const BOOL_P*)m_pData;  }

    inline_ DOUBLE* GetDoublePtr ()  {  return m_npSize < (INT_P)sizeof (DOUBLE) ? NULL : (DOUBLE*)m_pData;  }
    inline_ FLOAT* GetFloatPtr ()    {  return m_npSize < (INT_P)sizeof (FLOAT) ? NULL : (FLOAT*)m_pData;   }
    inline_ DWORD* GetDWordPtr ()    {  return m_npSize < (INT_P)sizeof (DWORD) ? NULL : (DWORD*)m_pData;   }
    inline_ WORD* GetWordPtr ()      {  return m_npSize < (INT_P)sizeof (WORD) ? NULL : (WORD*)m_pData;    }
    inline_ INT* GetIntPtr ()        {  return m_npSize < (INT_P)sizeof (INT) ? NULL : (INT*)m_pData;     }
    inline_ INT_P* GetIntPPtr ()     {  return m_npSize < (INT_P)sizeof (INT_P) ? NULL : (INT_P*)m_pData;   }
    inline_ UINT_P* GetUIntPPtr ()   {  return m_npSize < (INT_P)sizeof (UINT_P) ? NULL : (UINT_P*)m_pData;  }
    inline_ INT64* GetInt64Ptr ()    {  return m_npSize < (INT_P)sizeof (INT64) ? NULL : (INT64*)m_pData;   }
    inline_ UINT64* GetUInt64Ptr ()  {  return m_npSize < (INT_P)sizeof (UINT64) ? NULL : (UINT64*)m_pData;  }
    inline_ BOOL* GetBoolPtr ()      {  return m_npSize < (INT_P)sizeof (BOOL) ? NULL : (BOOL*)m_pData;    }
    inline_ BOOL_P* GetBoolPPtr ()   {  return m_npSize < (INT_P)sizeof (BOOL_P) ? NULL : (BOOL_P*)m_pData;  }

    inline_ INT_P GetCount_S_BYTE () const {  return m_npSize / (INT_P)sizeof (S_BYTE);  }
    inline_ INT_P GetCount_SHORT () const {  return m_npSize / (INT_P)sizeof (SHORT);  }
    inline_ INT_P GetCount_TCHAR () const {  return m_npSize / (INT_P)sizeof (TCHAR);  }
    inline_ INT_P GetCount_INT () const {  return m_npSize / (INT_P)sizeof (INT);  }
    inline_ INT_P GetCount_INT_P () const {  return m_npSize / (INT_P)sizeof (INT_P);  }
    inline_ INT_P GetCount_INT64 () const {  return m_npSize / (INT_P)sizeof (INT64);  }
    inline_ INT_P GetCount_FLOAT () const {  return m_npSize / (INT_P)sizeof (FLOAT);  }
    inline_ INT_P GetCount_DOUBLE () const {  return m_npSize / (INT_P)sizeof (DOUBLE);  }
    inline_ INT_P GetCount_BOOL () const {  return m_npSize / (INT_P)sizeof (BOOL);  }
    inline_ INT_P GetCount_CVolString () const { return 0; }

    #define _VOL_GET_BIN_DATA(npOffset, type)  \
        ASSERT (npOffset >= 0 && sizeof (type) <= sizeof (INT64));  \
        if (npOffset + (INT_P)sizeof (type) > m_npSize)  \
        {  \
            INT64 n64 = 0;  \
            COPY_MEM (&n64, m_pData + npOffset, MAX (0, m_npSize - npOffset));  \
            return *(type*)&n64;  \
        }  \
        return *(type*)(m_pData + npOffset)

    inline_ S_BYTE Get_S_BYTE (const INT_P npOffset) const {  _VOL_GET_BIN_DATA (npOffset, S_BYTE);  }
    inline_ SHORT Get_SHORT (const INT_P npOffset) const   {  _VOL_GET_BIN_DATA (npOffset, SHORT);   }
    inline_ TCHAR Get_TCHAR (const INT_P npOffset) const   {  _VOL_GET_BIN_DATA (npOffset, TCHAR);   }
    inline_ INT Get_INT (const INT_P npOffset) const       {  _VOL_GET_BIN_DATA (npOffset, INT);     }
    inline_ INT_P Get_INT_P (const INT_P npOffset) const   {  _VOL_GET_BIN_DATA (npOffset, INT_P);   }
    inline_ INT64 Get_INT64 (const INT_P npOffset) const   {  _VOL_GET_BIN_DATA (npOffset, INT64);   }
    inline_ FLOAT Get_FLOAT (const INT_P npOffset) const   {  _VOL_GET_BIN_DATA (npOffset, FLOAT);   }
    inline_ DOUBLE Get_DOUBLE (const INT_P npOffset) const {  _VOL_GET_BIN_DATA (npOffset, DOUBLE);  }
    inline_ BOOL Get_BOOL (const INT_P npOffset) const     {  _VOL_GET_BIN_DATA (npOffset, BOOL);    }
    CVolString Get_CVolString (const INT_P npOffset) const;

    #define _SET_BIN_BASE_DATA(data_type)  \
        inline_ void SetValue_##data_type (const INT_P npOffset, const data_type value)  \
        {  \
            ASSERT (IsOffsetInside (npOffset, sizeof (data_type)));  \
            *(data_type*)(m_pData + npOffset) = value;  \
        }

    _SET_BIN_BASE_DATA (S_BYTE)
    _SET_BIN_BASE_DATA (SHORT)
    _SET_BIN_BASE_DATA (TCHAR)
    _SET_BIN_BASE_DATA (INT)
    _SET_BIN_BASE_DATA (INT64)
    _SET_BIN_BASE_DATA (DOUBLE)
    _SET_BIN_BASE_DATA (FLOAT)
    _SET_BIN_BASE_DATA (BOOL)

    #define _ADD_BIN_BASE_DATA(data_type)  \
        inline_ void AddValue_##data_type (const data_type value)  \
        {  \
            Append ((void*)&value, sizeof (data_type));   \
        }

    _ADD_BIN_BASE_DATA (S_BYTE)
    _ADD_BIN_BASE_DATA (SHORT)
    _ADD_BIN_BASE_DATA (TCHAR)
    _ADD_BIN_BASE_DATA (INT)
    _ADD_BIN_BASE_DATA (INT64)
    _ADD_BIN_BASE_DATA (DOUBLE)
    _ADD_BIN_BASE_DATA (FLOAT)
    _ADD_BIN_BASE_DATA (BOOL)

    #define _INSERT_BIN_BASE_DATA(data_type)  \
        inline_ void InsertValue_##data_type (const INT_P npOffset, const data_type value)  \
            {  \
                Insert (npOffset, (void*)&value, sizeof (data_type));  \
            }

    _INSERT_BIN_BASE_DATA (S_BYTE)
    _INSERT_BIN_BASE_DATA (SHORT)
    _INSERT_BIN_BASE_DATA (TCHAR)
    _INSERT_BIN_BASE_DATA (INT)
    _INSERT_BIN_BASE_DATA (INT64)
    _INSERT_BIN_BASE_DATA (DOUBLE)
    _INSERT_BIN_BASE_DATA (FLOAT)
    _INSERT_BIN_BASE_DATA (BOOL)
    void InsertTextValue (const INT_P npOffset, const TCHAR* ps, const BOOL_P blpInsertEndZeroChar);

    void AddTextValue (const TCHAR* ps, const BOOL_P blpAddEndZeroChar);

    template <typename T>
    inline_ void AllocUserObject (T** ppUserObject)
    {
        ASSERT_RW_ADR (ppUserObject, sizeof (T*));
        *ppUserObject = (T*)Alloc (sizeof (T));
    }

    template <typename T>
    inline_ void AddUserObjectSpace (T** ppUserObject, const BOOL_P blpZero)
    {
        ASSERT_RW_ADR (ppUserObject, sizeof (T*));
        *ppUserObject = (T*)AddSpace (sizeof (T), blpZero);
    }

    template <typename T>
    inline_ void AddUserObject (const T* pUserObject)
    {
        Append (pUserObject, sizeof (T));
    }

    template <typename T>
    inline_ void InsertUserObject (const INT_P npOffset, const T* pUserObject)
    {
        Insert (npOffset, pUserObject, sizeof (T));
    }

    template <typename T>
    inline_ const T* cGetUserObjectPtr (const T** ppUserObject) const
    {
        ASSERT_RW_ADR (ppUserObject, sizeof (T*));
        return (*ppUserObject = (const T*)GetPtr ());
    }

    template <typename T>
    inline_ T* GetUserObjectPtr (T** ppUserObject)
    {
        ASSERT_RW_ADR (ppUserObject, sizeof (T*));
        return (*ppUserObject = (T*)GetPtr ());
    }

    // 返回最后一个用户对象,如果不存在则返回NULL.
    template <typename T>
    inline_ const T* cGetLastUserObjectPtr (const T** ppLastUserObject) const
    {
        ASSERT_RW_ADR (ppLastUserObject, sizeof (T*));
        return (*ppLastUserObject = (m_npSize < (INT_P)sizeof (T) ? NULL : (const T*)(m_pData + m_npSize - sizeof (T))));
    }

    template <typename T>
    inline_ T* GetLastUserObjectPtr (T** ppLastUserObject)
    {
        ASSERT_RW_ADR (ppLastUserObject, sizeof (T*));
        return (*ppLastUserObject = (m_npSize < (INT_P)sizeof (T) ? NULL : (T*)(m_pData + m_npSize - sizeof (T))));
    }

    inline_ const TCHAR* GetTextPtr () const
    {
        return (const TCHAR*)GetPtr ();
    }
    inline_ TCHAR* GetTextPtr ()
    {
        return (TCHAR*)GetPtr ();
    }

    // 查找所指定的字节集内容,找到返回其偏移位置,未找到返回-1.
    INT_P FindBin (const BYTE* pFindBin, const INT_P npFindBinSize, INT_P npBeginOffset) const;
    inline_ INT_P FindBin (const CVolMem& binFind, INT_P npBeginOffset) const
    {
        return FindBin (binFind.GetPtr (), binFind.GetSize (), npBeginOffset);
    }

    // 倒找所指定的字节集内容,找到返回其偏移位置,未找到返回-1.
    INT_P ReverseFindBin (const BYTE* pFindBin, const INT_P npFindBinSize, INT_P npBeginOffset) const;
    inline_ INT_P ReverseFindBin (const CVolMem& binFind, INT_P npBeginOffset) const
    {
        return ReverseFindBin (binFind.GetPtr (), binFind.GetSize (), npBeginOffset);
    }

    // 将本字节集中的由pFindBin和npFindBinSize指定的子字节集内容替换为pReplaceBin和npReplaceBinSize指定的字节集内容
    void ReplaceBin (const BYTE* pFindBin, const INT_P npFindBinSize,
            const BYTE* pReplaceBin, const INT_P npReplaceBinSize, INT_P npBeginOffset, INT_P npReplaceTimes);
    inline_ void ReplaceBin (const CVolMem& binFind, const CVolMem& binReplace, const INT_P npBeginOffset, const INT_P npReplaceTimes)
    {
        ReplaceBin (binFind.GetPtr (), binFind.GetSize (), binReplace.GetPtr (),
                binReplace.GetSize (), npBeginOffset, npReplaceTimes);
    }

    // 将本字节集进行分割,将分割后的所有子字节集存放入aryResultBin参数所指定的数组对象中,返回所存放进去的子字节集数目.
    INT_P SplitBin (const BYTE* pFindBin, const INT_P npFindBinSize, INT_P npMaxNumResultBin, CVolObjectArray& aryResultBin);
    inline_ INT_P SplitBin (const CVolMem& binFind, const INT_P npMaxNumResultBin, CVolObjectArray& aryResultBin)
    {
        return SplitBin (binFind.GetPtr (), binFind.GetSize (), npMaxNumResultBin, aryResultBin);
    }

    inline_ INT_P GetNumUserObjects (const INT_P npUserObjectSize) const
    {
        ASSERT (npUserObjectSize > 0 && (m_npSize % npUserObjectSize) == 0);
        return m_npSize / npUserObjectSize;
    }

    // 从文件中读入指定尺寸的数据,返回所实际读入数据尺寸,失败返回-1.
    // npReadDataSize为-1表示读入全部
    INT_P ReadFromFile (const TCHAR* szFileName, INT_P npReadDataSize = -1);

    // 将指定尺寸的数据写入文件中,成功返回真,失败返回假.
    //   npWriteDataSize: 为-1表示写入全部
    BOOL_P WriteIntoFile (const TCHAR* szFileName, INT_P npWriteDataSize = -1) const;

    inline_ BOOL operator== (const CVolMem& memCompare) const
    {
        return IsEqual (memCompare);
    }
    inline_ BOOL operator!= (const CVolMem& memCompare) const
    {
        return (IsEqual (memCompare) == FALSE);
    }

    HGLOBAL ToGlobalMem () const;
    CVolString& ToHexStr (CVolString& strResult);
    CVolMem& AppendFromHexStr (const TCHAR* szHexStr);

    inline_ static CVolMem& sFromHexStr (const TCHAR* szHexStr, CVolMem& memResult)
    {
        return memResult.AppendFromHexStr (szHexStr);
    }

    //----------------------------------------------------------------------

private:
    BYTE* _NAME_COMPILER_AGREED (m_pData);
    INT_P m_npAllocedSize, _NAME_COMPILER_AGREED (m_npSize);
    INT_P m_npMemAlignSize;  // 如果小于等于0,则默认为_DEFAULT_MEM_ALIGN_SIZE.
};

#endif
