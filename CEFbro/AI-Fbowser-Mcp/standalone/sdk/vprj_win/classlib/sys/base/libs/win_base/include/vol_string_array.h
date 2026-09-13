
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_STRING_ARRAY_H__
#define __VOL_STRING_ARRAY_H__

class CVolBaseInputStream;
class CVolBaseOutputStream;

class CMStringArray : public CVolCommonBaseWithMemManager
{
    DECLARE_BASE_CLASS (CMStringArray)

public:
    inline_ CMStringArray (const INT_P npAlignElementCount = 32)
    {
        SetAlignElementCount (npAlignElementCount);
    }

    inline_ ~CMStringArray ()
    {
        RemoveAll ();
    }

    inline_ void SetAlignElementCount (const INT_P npAlignElementCount)
    {
        ASSERT (npAlignElementCount >= 0);
        m_mem.SetMemAlignSize (sizeof (TCHAR*) * npAlignElementCount);
    }
    inline_ INT_P GetAlignElementCount () const
    {
        return m_mem.GetMemAlignSize () / sizeof (TCHAR*);
    }

    inline_ INT_P GetCount () const
    {
        ASSERT (m_mem.GetSize () % sizeof (TCHAR*) == 0);
        return m_mem.GetSize () / sizeof (TCHAR*);
    }

    inline_ INT_P GetUpperBound () const
    {
        return GetCount () - 1;
    }

    // 返回指定索引值是否在本数组内有效
    inline_ BOOL_P IsIndexValid (const INT_P npIndex) const
    {
        return (npIndex >= 0 && npIndex < GetCount ());
    }

    inline_ BOOL_P IsEmpty () const
    {
        return m_mem.IsEmpty ();
    }

    void RemoveAll ();

    inline_ TCHAR** GetData ()
    {
        return (TCHAR**)m_mem.GetPtr ();
    }

    inline_ const TCHAR** GetData () const
    {
        return (const TCHAR**)m_mem.GetPtr ();
    }

    inline_ const TCHAR* GetAt (const INT_P npIndex) const
    {
        ASSERT (IsIndexValid (npIndex));

        const TCHAR* ps = GetData () [npIndex];
        return (ps == NULL ? _T ("") : ps);
    }

    inline_ const TCHAR* operator[] (const INT_P npIndex) const
    {
        ASSERT (IsIndexValid (npIndex));

        const TCHAR* ps = GetData () [npIndex];
        return (ps == NULL ? _T ("") : ps);
    }

    // 将nIndex1和nIndex2这两个位置的内容互换
    // 注意本方法不能重分配内存
    void XchgElement (const INT_P npIndex1, const INT_P npIndex2);

    void Append (const CMStringArray& src);

    // 将src中的所有不在本数组中存在的成员加入本数组
    void UniqueAppend (const CMStringArray& src);
    void IUniqueAppend (const CMStringArray& src);

    // 删除本数组中所有在saryTest中存在的成员
    void RemoveDuplicated (const CMStringArray& saryTest);
    void IRemoveDuplicated (const CMStringArray& saryTest);

    inline_ void Copy (const CMStringArray& src)
    {
        if (&src.m_mem != &m_mem)
        {
            RemoveAll ();
            Append (src);
        }
        ELSE_FAIL
    }

    void RemoveAt (const INT_P npIndex, const INT_P npCount = 1);
    BOOL_P RemoveElement (const TCHAR* ps);

    inline_ void SetAt (const INT_P npIndex, const TCHAR* szElement)
    {
        ASSERT (IsIndexValid (npIndex));
        SetAt_NotClone (npIndex, CloneText (szElement));
    }

    inline_ void Add (const TCHAR* szElement)
    {
        Add_NotClone (CloneText (szElement));
    }

    inline_ INT_P Add2 (const TCHAR* szElement)
    {
        Add_NotClone (CloneText (szElement));
        return GetCount () - 1;
    }

    inline_ const TCHAR* Add3 (const TCHAR* szElement)
    {
        Add_NotClone (CloneText (szElement));
        return GetAt (GetCount () - 1);
    }

    INT_P Add4 (const INT_P npNumParams, ...)
    {
        va_list argList;
        va_start (argList, npNumParams);

        for (INT_P npParamIndex = 0; npParamIndex < npNumParams; npParamIndex++)
            Add (va_arg (argList, TCHAR*));

        va_end (argList);
        return GetCount () - npNumParams;
    }

    inline_ void Add (const TCHAR* szElement, const INT_P npLen)
    {
        Add_NotClone (CloneText (szElement, npLen));
    }

    inline_ INT_P Add2 (const TCHAR* szElement, const INT_P npLen)
    {
        Add_NotClone (CloneText (szElement, npLen));
        return GetCount () - 1;
    }

    inline_ const TCHAR* Add3 (const TCHAR* szElement, const INT_P npLen)
    {
        Add_NotClone (CloneText (szElement, npLen));
        return GetAt (GetCount () - 1);
    }

    inline_ void UniqueAdd (const TCHAR* szElement)
    {
        if (IsElementExist (szElement) == FALSE)
            Add (szElement);
    }

    inline_ void IUniqueAdd (const TCHAR* szElement)
    {
        if (IIsElementExist (szElement) == FALSE)
            Add (szElement);
    }

    inline_ void InsertAt (const INT_P npIndex, const TCHAR* szElement)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount ());
        InsertAt_NotClone (npIndex, CloneText (szElement));
    }

    inline_ void InsertAt (const INT_P npIndex, const TCHAR* szElement, const INT_P npLen)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount ());
        InsertAt_NotClone (npIndex, CloneText (szElement, npLen));
    }

#ifdef _UNICODE
    inline_ void SetAt (const INT_P npIndex, const U8CHAR* szElement)
    {
        ASSERT (IsIndexValid (npIndex));
        CVolMem memBuf;
        SetAt (npIndex, ConvertText (szElement, memBuf));
    }

    inline_ void Add (const U8CHAR* szElement)
    {
        CVolMem memBuf;
        Add (ConvertText (szElement, memBuf));
    }

    inline_ INT_P Add2 (const U8CHAR* szElement)
    {
        CVolMem memBuf;
        Add (ConvertText (szElement, memBuf));
        return GetCount () - 1;
    }

    inline_ void InsertAt (const INT_P npIndex, const U8CHAR* szElement)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount ());
        CVolMem memBuf;
        InsertAt (npIndex, ConvertText (szElement, memBuf));
    }
#endif

    INT_P FindFirstElement (const TCHAR* ps) const;
    INT_P FindLastElement (const TCHAR* ps) const;
    INT_P IFindFirstElement (const TCHAR* ps) const;
    INT_P IFindLastElement (const TCHAR* ps) const;

    inline_ BOOL_P IsElementExist (const TCHAR* ps) const
    {
        return (FindFirstElement (ps) != -1);
    }

    inline_ BOOL_P IIsElementExist (const TCHAR* ps) const
    {
        return (IFindFirstElement (ps) != -1);
    }

    // 将所有szOldText文本替换为szNewText文本,区分大小写.
    // 返回是否进行了实际替换
    BOOL_P ReplaceAllElements (const TCHAR* szOldText, const TCHAR* szNewText);
    // 将所有szOldText文本替换为szNewText文本,不区分大小写.
    // 返回是否进行了实际替换
    BOOL_P IReplaceAllElements (const TCHAR* szOldText, const TCHAR* szNewText);

    // 返回本数组对象的内容是否与sary中的一致
    //   blpIgnoreCase: 比较时是否忽略大小写
    BOOL_P IsEqual (const CMStringArray& sary, const BOOL_P blpIgnoreCase) const;

    void LoadFromStream (CVolBaseInputStream& stream);
    void SaveIntoStream (CVolBaseOutputStream& stream);

    friend CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, CMStringArray& strary);
    friend CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const CMStringArray& strary);

    void GetDumpString (CVolString& strDump, INT nMaxDumpSize);

protected:
    //!! 如果wszText/szText为NULL,则必须返回NULL,否则会导致释放所复制的指针错误.
    WCHAR* CloneText (const WCHAR* wszText, const INT_P npLen);
    U8CHAR* CloneText (const U8CHAR* szText, const INT_P npLen);

    inline_ WCHAR* CloneText (const WCHAR* wszText)
    {
        ASSERT_R_STR_OR_NULL (wszText);
        return (wszText == NULL ? NULL : CloneText (wszText, wcslen (wszText)));
    }

    inline_ U8CHAR* CloneText (const U8CHAR* szText)
    {
        ASSERT_R_STR_OR_NULL (szText);
        return (szText == NULL ? NULL : CloneText (szText, strlen (szText)));
    }

    void SetAt_NotClone (const INT_P npIndex, const TCHAR* szElement);

    inline_ void Add_NotClone (const TCHAR* szElement)
    {
        ASSERT_R_STR_OR_NULL (szElement);
        m_mem.Append (&szElement, sizeof (TCHAR*));
    }

    inline_ INT_P Add_NotClone2 (const TCHAR* szElement)
    {
        ASSERT_R_STR_OR_NULL (szElement);
        m_mem.Append (&szElement, sizeof (TCHAR*));
        return GetCount () - 1;
    }

    inline_ void InsertAt_NotClone (const INT_P npIndex, const TCHAR* szElement)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount ());
        ASSERT_R_STR_OR_NULL (szElement);
        m_mem.Insert (npIndex * sizeof (TCHAR*), (BYTE*)&szElement, sizeof (TCHAR*));
    }

    inline_ void InsertAt_NotClone (const INT_P npIndex, CMStringArray& src)  // src will be emptied
    {
        m_mem.Insert (npIndex * sizeof (TCHAR*), src.m_mem.GetPtr (), src.m_mem.GetSize ());
        src.m_mem.Free ();
    }

    inline_ void Append_NotClone (CMStringArray& src)  // src will be emptied
    {
        m_mem.Append (src.m_mem);
        src.m_mem.Free ();
    }

    inline_ void Append_NotClone (CMStringArray* psrc)  // psrc will be emptied
    {
        ASSERT_R_DATA (psrc);
        m_mem.Append (psrc->m_mem);
        psrc->m_mem.Free ();
    }

    inline_ void Copy_NotClone (CMStringArray& src)  // src will be emptied
    {
        RemoveAll ();
        Append_NotClone (src);
    }

    inline_ void RemoveAt_NotDelete (const INT_P npIndex, const INT_P npCount = 1)
    {
        ASSERT (npIndex >= 0 && npIndex + npCount <= GetCount ());
        m_mem.Remove (npIndex * sizeof (TCHAR*), sizeof (TCHAR*) * npCount);
    }

protected:
    CVolMem m_mem;
};

// 文本排序数组(大小写相关)
class CMStringSortArray : public CVolCommonBase
{
    DECLARE_BASE_CLASS (CMStringSortArray)

public:
    inline_ CMStringSortArray (const INT_P npAlignElementCount = 32)
    {
        SetAlignElementCount (npAlignElementCount);
    }

    inline_ void SetAlignElementCount (const INT_P npAlignElementCount)
    {
        ASSERT (npAlignElementCount >= 0);
        m_sary.SetAlignElementCount (npAlignElementCount);
    }
    inline_ INT_P GetAlignElementCount () const
    {
        return m_sary.GetAlignElementCount ();
    }

    inline_ INT_P GetCount () const
    {
        return m_sary.GetCount ();
    }

    inline_ INT_P GetUpperBound () const
    {
        return m_sary.GetUpperBound ();
    }

    // 返回指定索引值是否在本数组内有效
    inline_ BOOL_P IsIndexValid (const INT_P npIndex) const
    {
        return (npIndex >= 0 && npIndex < GetCount ());
    }

    inline_ BOOL_P IsEmpty () const
    {
        return m_sary.IsEmpty ();
    }

    inline_ void RemoveAll ()
    {
        m_sary.RemoveAll ();
    }

    inline_ void RemoveAt (const INT_P npIndex, const INT_P npCount = 1)
    {
        m_sary.RemoveAt (npIndex, npCount);
    }

    inline_ const TCHAR** GetData () const
    {
        return m_sary.GetData ();
    }

    inline_ const CMStringArray& StringArray () const
    {
        return m_sary;
    }
    inline_ CMStringArray& StringArray ()
    {
        return m_sary;
    }

    // 如果从外部导入了未排序数据,可以调用本方法进行手动排序.
    // 其它情况下不需要调用本方法
    void Sort ();

    // 与Sort方法不同之处在于本方法除了排序还会将删除掉多余的重复项目(相同项目只保留一个)
    void SortAndEnsureUnique ();

    inline_ const TCHAR* GetAt (const INT_P npIndex) const
    {
        return m_sary.GetAt (npIndex);
    }

    inline_ const TCHAR* operator[] (const INT_P npIndex) const
    {
        return m_sary.GetAt (npIndex);
    }

    inline_ void Copy (const CMStringSortArray& src)
    {
        m_sary.Copy (src.m_sary);
    }

    inline_ BOOL_P IsEqual (const INT_P npIndex, const TCHAR* data) const
    {
        ASSERT (npIndex >= 0 && npIndex < m_sary.GetCount ());
        ASSERT_R_STR_OR_NULL (data);
        return (compare (m_sary [npIndex], data) == 0);
    }

    // 返回本数组对象的内容是否与sary中的一致
    BOOL_P IsEqual (const CMStringSortArray& sary) const;

    // 将指定数据加入数组,返回所加入位置的索引.
    // 注意! 此加入成员的索引位置不是固定的,其很可能会被后续成员加入操作更改.
    virtual INT_P Add (const TCHAR* data)
    {
        return Add (data, FALSE);
    }

    // 加入字符串对象的内容
    inline_ INT_P Add (const CVolString& str)
    {
        return Add (str.GetText ());
    }

    // 将指定数据加入数组,返回所加入位置的索引.
    // 如果存在同等成员且blpAddAtEnd参数为真,则加在同等成员的尾部.
    // 注意! 此加入成员的索引位置不是固定的,其很可能会被后续成员加入操作更改.
    INT_P Add (const TCHAR* data, const BOOL_P blpAddAtEnd);

    INT_P Add2 (const INT_P npNumParams, ...)
    {
        ASSERT (npNumParams > 0);

        va_list argList;
        va_start (argList, npNumParams);

        const INT_P npFirstIndex = Add (va_arg (argList, TCHAR*));

        for (INT_P npParamIndex = 1; npParamIndex < npNumParams; npParamIndex++)
            Add (va_arg (argList, TCHAR*));

        va_end (argList);
        return npFirstIndex;
    }

    // 寻找指定成员，找到返回其索引位置，否则返回-1. 
    // 注意: 所找到的可能并非第一个等于该值的成员
    INT_P FindElement (const TCHAR* data) const;

    // 返回第一个等于指定数据的成员的索引位置，如果没找到则返回-1. 
    INT_P FindFirstElement (const TCHAR* data) const;

    // 返回最后一个等于指定数据的成员的索引位置，如果没找到则返回-1. 
    // 注意: 数组必须处于完全排序状态
    INT_P FindLastElement (const TCHAR* data) const;

    inline_ void GetDumpString (CVolString& strDump, INT nMaxDumpSize)
    {
        m_sary.GetDumpString (strDump, nMaxDumpSize);
    }

    //-------------------------------------------------------

    void LoadFromStream (CVolBaseInputStream& stream);
    void SaveIntoStream (CVolBaseOutputStream& stream);

    friend CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const CMStringSortArray& ary);
    friend CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, CMStringSortArray& ary);

protected:
    virtual INT_P compare (const TCHAR* element1, const TCHAR* element2) const
    {
        return _tcscmp (
                (element1 == NULL ? _T ("") : element1),
                (element2 == NULL ? _T ("") : element2));
    }

protected:
    CMStringArray m_sary;  // 记录所有文本成员值的有序数组
};

// 只能加入唯一值的文本数组(大小写相关)
class CUniqueStringArray : public CMStringSortArray
{
    DECLARE_DERIVED_CLASS (CUniqueStringArray)

public:
    inline_ CUniqueStringArray ()
    {
    }

    inline_ CUniqueStringArray (const INT_P npAlignElementCount) :
            CMStringSortArray (npAlignElementCount)
    {
    }

    // 将指定数据加入数组，如果值已经存在返回-1,否则返回所加入位置的索引. 
    // 注意! 此加入成员的索引位置不是固定的，其很可能会被后续成员加入操作更改. 
    virtual INT_P Add (const TCHAR* data) override
    {
        return Add (data, NULL);
    }

    // 将指定数据加入数组，如果值已经存在返回-1,否则返回所加入位置的索引. 
    // 如果pnpExistElementIndex不为NULL，则在pnpExistElementIndex中返回该成员的位置索引（存在返回以前的，不存在返回新加入的）. 
    // 注意! 此加入成员的索引位置不是固定的，其很可能会被后续成员加入操作更改. 
    INT_P Add (const TCHAR* data, INT_P* pnpExistElementIndex);
};

// 文本排序数组(大小写无关)
class CIStringSortArray : public CMStringSortArray
{
    DECLARE_DERIVED_CLASS (CIStringSortArray)

public:
    inline_ CIStringSortArray ()
    {
    }

    inline_ CIStringSortArray (const INT_P npAlignElementCount) :
            CMStringSortArray (npAlignElementCount)
    {
    }

protected:
    virtual INT_P compare (const TCHAR* element1, const TCHAR* element2) const
    {
        return _tcsicmp (
                (element1 == NULL ? _T ("") : element1),
                (element2 == NULL ? _T ("") : element2));
    }
};

// 只能加入唯一值的文本数组(大小写无关)
class CIUniqueStringArray : public CUniqueStringArray
{
    DECLARE_DERIVED_CLASS (CIUniqueStringArray)

public:
    inline_ CIUniqueStringArray ()
    {
    }

    inline_ CIUniqueStringArray (const INT_P npAlignElementCount) :
            CUniqueStringArray (npAlignElementCount)
    {
    }

protected:
    virtual INT_P compare (const TCHAR* element1, const TCHAR* element2) const
    {
        return _tcsicmp (
                (element1 == NULL ? _T ("") : element1),
                (element2 == NULL ? _T ("") : element2));
    }
};

#endif
