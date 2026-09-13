
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_ARRAY_H__
#define __VOL_ARRAY_H__

template <class T> class CMArray : public CVolCommonBase
{
public:
    inline_ CMArray (const INT_P npAlignElementCount = 32)
    {
        ASSERT (npAlignElementCount >= 0);
        SetAlignElementCount (npAlignElementCount);
    }

    inline_ void SetAlignElementCount (const INT_P npAlignElementCount)
    {
        ASSERT (npAlignElementCount >= 0);
        m_mem.SetMemAlignSize (npAlignElementCount * sizeof (T));
    }
    inline_ INT_P GetAlignElementCount () const
    {
        return m_mem.GetMemAlignSize () / sizeof (T);
    }

    inline_ INT_P GetCount () const
    {
        return m_mem.GetSize () / sizeof (T);
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

    inline_ INT_P GetUpperBound () const
    {
        return GetCount () - 1;
    }

    inline_ void RemoveAll ()
    {
        m_mem.Free ();
    }

    inline_ T* InitCount (const INT_P npNumElements, const BOOL_P blpZero)
    {
        ASSERT (npNumElements >= 0);

        T* pElement = (T*)m_mem.Alloc (npNumElements * sizeof (T));
        if (blpZero)
            ZERO_MEM (pElement, npNumElements * sizeof (T));
        return pElement;
    }

    inline_ BOOL_P IsAtEnd (const T* pData) const
    {
        return m_mem.IsAtEnd (pData);
    }

    inline_ void Zero ()
    {
        m_mem.Zero ();
    }

    inline_ T* GetData ()
    {
        return (T*)m_mem.GetPtr ();
    }

    inline_ const T* GetData () const
    {
        return (const T*)m_mem.GetPtr ();
    }

    inline_ INT_P GetDataSize () const
    {
        return m_mem.GetSize ();
    }

    inline_ const T& GetAt (const INT_P npIndex) const
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () [npIndex];
    }

    inline_ T& GetAt (const INT_P npIndex)
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () [npIndex];
    }

    inline_ T GetElementAt (const INT_P npIndex) const
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () [npIndex];
    }

    inline_ T* GetElementData (const INT_P npIndex)
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () + npIndex;
    }

    inline_ const T* GetElementData (const INT_P npIndex) const
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () + npIndex;
    }

    inline_ INT_P GetOneElementSize () const
    {
        return sizeof (T);
    }

    inline_ const T& operator[] (const INT_P npIndex) const
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () [npIndex];
    }

    inline_ T& operator[] (const INT_P npIndex)
    {
        ASSERT (IsIndexValid (npIndex));
        return GetData () [npIndex];
    }

    inline_ void SetAt (const INT_P npIndex, const T& element)
    {
        ASSERT (IsIndexValid (npIndex));
        GetData () [npIndex] = element;
    }

    inline_ void Append (const CMArray<T>& src)
    {
        if (&src.m_mem != &m_mem)
            m_mem.Append (src.m_mem);
        ELSE_FAIL
    }

    inline_ T* AddEmptyElements (const INT_P npNumElements, const BOOL_P blpZero = FALSE)
    {
        ASSERT (npNumElements >= 0);
        return (T*)m_mem.AddSpace (npNumElements * sizeof (T), blpZero);
    }

    inline_ void Append (const CMArray<T>& src, const INT_P npBeginIndex, const INT_P npCount)
    {
        ASSERT (npBeginIndex >= 0 && npCount >= 0 && npBeginIndex + npCount <= src.GetCount ());
        if (&src.m_mem != &m_mem)
            m_mem.Append (src.GetData () + npBeginIndex, npCount * sizeof (T));
        ELSE_FAIL
    }

    inline_ void Append (const CMArray<T>* psrc)
    {
        ASSERT_R_DATA (psrc);
        if (&psrc->m_mem != &m_mem)
            m_mem.Append (psrc->m_mem);
        ELSE_FAIL
    }

    inline_ void Append (const T* pBegin, const INT_P npCount)
    {
        ASSERT_R_ADR (pBegin, npCount * sizeof (T));
        m_mem.Append (pBegin, npCount * sizeof (T));
    }

    inline_ void Copy (const T* pBegin, const INT_P npCount)
    {
        ASSERT_R_ADR (pBegin, npCount * sizeof (T));
        m_mem.CopyFrom (pBegin, npCount * sizeof (T));
    }

    inline_ void Copy (const CMArray<T>& src)
    {
        if (&src.m_mem != &m_mem)
            m_mem.CopyFrom (src.m_mem);
        ELSE_FAIL
    }

    inline_ CVolMem& GetMem ()
    {
        return m_mem;
    }
    inline_ const CVolMem& GetMem () const
    {
        return m_mem;
    }

    inline_ void Add (const T& element)
    {
        m_mem.Append (&element, sizeof (T));
    }

    inline_ INT_P Add2 (const T& element)
    {
        m_mem.Append (&element, sizeof (T));
        return GetCount () - 1;
    }

    INT_P Add3 (const TCHAR* szParamTypes, ...)
    {
        const INT_P npFirstIndex = GetCount ();

        va_list argList;
        va_start (argList, szParamTypes);

        const INT_P npNumParams = _tcslen (szParamTypes);
        for (INT_P npParamIndex = 0; npParamIndex < npNumParams; npParamIndex++)
        {
            T var;
            switch (szParamTypes [npParamIndex])
            {
            case _C_VOL_SBYTE:  // 字节
                var = (T)va_arg (argList, S_BYTE);
                break;
            case _C_VOL_SHORT:  // 短整数
                var = (T)va_arg (argList, SHORT);
                break;
            case _C_VOL_WCHAR:  // 字符
                var = (T)va_arg (argList, TCHAR);
                break;
            case _C_VOL_INT:  // 整数
                var = (T)va_arg (argList, INT);
                break;
            case _C_VOL_VINT:  // 变整数
            case _C_VOL_METHOD:  // 方法名
                var = (T)va_arg (argList, INT_P);
                break;
            case _C_VOL_LONG:  // 长整数
                var = (T)va_arg (argList, INT64);
                break;
            case _C_VOL_FLOAT:  // 单精度小数, FLOAT在VC中是使用DOUBLE方式传递的.
            case _C_VOL_DOUBLE:  // 小数
                var = (T)va_arg (argList, DOUBLE);
                break;
            case _C_VOL_BOOL:  // 逻辑值
                var = (T)va_arg (argList, BOOL);
                break;
            default:
                FAIL;  // 仅支持基本数据类型
                var = 0;
                break;
            }
            m_mem.Append (&var, sizeof (T));
        }

        va_end (argList);
        return npFirstIndex;
    }

    inline_ void InsertAt (const INT_P npIndex, const T& element)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount ());
        m_mem.Insert (npIndex * sizeof (T), &element, sizeof (T));
    }

    inline_ void InsertAt (const INT_P npIndex, const T* pElements, const INT_P npNumElements)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount () && npNumElements >= 0);
        ASSERT_R_ADR (pElements, sizeof (T) * npNumElements);
        m_mem.Insert (npIndex * sizeof (T), pElements, sizeof (T) * npNumElements);
    }

    inline_ void InsertAt (const INT_P npIndex, const CMArray<T>& src)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount ());
        if (&src.m_mem != &m_mem)
            m_mem.Insert (npIndex * sizeof (T), src.m_mem.GetPtr (), src.m_mem.GetSize ());
        ELSE_FAIL
    }

    inline_ void InsertAt (const INT_P npIndex, const CMArray<T>& src, const INT_P npBeginIndex, const INT_P npCount)
    {
        ASSERT (npIndex >= 0 && npIndex <= GetCount () &&
                npBeginIndex >= 0 && npCount >= 0 && npBeginIndex + npCount <= src.GetCount ());
        if (&src.m_mem != &m_mem)
            m_mem.Insert (npIndex * sizeof (T), src.GetData () + npBeginIndex, npCount * sizeof (T));
        ELSE_FAIL
    }

    inline_ void RemoveAt (const INT_P npIndex, const INT_P npCount = 1)
    {
        ASSERT (npIndex >= 0 && npCount >= 0 && npIndex + npCount <= GetCount ());
        m_mem.Remove (npIndex * sizeof (T), sizeof (T) * npCount);
    }

    inline_ void RemoveToEnd (const INT_P npBeginIndex)
    {
        ASSERT (npBeginIndex >= 0 && npBeginIndex <= GetCount ());
        m_mem.Realloc (npBeginIndex * sizeof (T));
    }

    inline_ BOOL_P RemoveElement (const T& data)
    {
        const INT_P npIndex = FindElement (data);
        if (npIndex != -1)
        {
            RemoveAt (npIndex);
            return TRUE;
        }

        return FALSE;
    }

    inline_ void XchgElement (const INT_P npElementIndex1, const INT_P npElementIndex2)
    {
        ASSERT (IsIndexValid (npElementIndex1) && IsIndexValid (npElementIndex2));

        if (npElementIndex1 != npElementIndex2)
        {
            T* ap = GetData ();
            const T bak = ap [npElementIndex1];
            ap [npElementIndex1] = ap [npElementIndex2];
            ap [npElementIndex2] = bak;
        }
    }

    inline_ void Push (const T& element)
    {
        m_mem.Append (&element, sizeof (T));
    }

    inline_ T Pop ()
    {
        const INT_P npNewSize = m_mem.GetSize () - sizeof (T);
        ASSERT (npNewSize >= 0);
        T data = *(T*)(m_mem.GetPtr () + npNewSize);
        m_mem.Realloc (npNewSize);
        return data;
    }

    inline_ void Pop (T* pPopedData)
    {
        ASSERT_RW_DATA (pPopedData);
        const INT_P npNewSize = m_mem.GetSize () - sizeof (T);
        ASSERT (npNewSize >= 0);
        COPY_MEM (pPopedData, m_mem.GetPtr () + npNewSize, sizeof (T));
        m_mem.Realloc (npNewSize);
    }

    inline_ void CheckPopDiscard ()
    {
        const INT_P npNewSize = m_mem.GetSize () - sizeof (T);
        m_mem.Realloc (MAX (0, npNewSize));
    }

    inline_ T GetLastElement ()
    {
        const INT_P npNewSize = m_mem.GetSize () - sizeof (T);
        ASSERT (npNewSize >= 0);
        return *(T*)(m_mem.GetPtr () + npNewSize);
    }

    INT_P FindElement (const T& data) const
    {
        const INT_P npCount = GetCount ();
        const T* p = GetData ();
        for (INT_P i = 0; i < npCount; i++, p++)
        {
            if (*p == data)
                return i;
        }
        ASSERT (p == GetData () + npCount);
        return -1;
    }

    inline_ BOOL_P IsElementExist (const T& data) const
    {
        return (FindElement (data) != -1);
    }

    INT_P ReverseFindElement (const T& data) const
    {
        const INT_P npCount = GetCount ();
        const T* p = GetData () + npCount - 1;
        for (INT_P i = npCount - 1; i >= 0; i--, p--)
        {
            if (*p == data)
                return i;
        }
        ASSERT (p == GetData () - 1);
        return -1;
    }

    // 将所有dataOld数据替换为dataNew
    // 返回是否进行了实际替换
    BOOL_P ReplaceAllElements (const T& dataOld, const T& dataNew)
    {
        BOOL_P blpReplaced = FALSE;

        const INT_P npCount = GetCount ();
        T* p = GetData ();
        for (INT_P i = 0; i < npCount; i++, p++)
        {
            if (*p == dataOld)
            {
                *p = dataNew;
                blpReplaced = TRUE;
            }
        }

        return blpReplaced;
    }

    // 返回本数组对象的内容是否与ary中的一致
    inline_ BOOL_P IsEqual (const CMArray<T>& ary) const
    {
        return m_mem.IsEqual (ary.m_mem);
    }

    // blpAscend: 排序方向是否从小到大
    void Sort (const BOOL_P blpAscend)  // 希尔排序法
    {
        T* pElement = GetData ();
        const INT_P npCount = GetCount ();

        INT_P npIndex = npCount / 2;
        while (npIndex >= 1)
        {
            for (INT_P i = npIndex; i < npCount; i++)
            {
                T temp = pElement [i];

                INT_P j;
                for (j = i - npIndex; j >= 0 && (blpAscend ? temp < pElement [j] : temp > pElement [j]); j -= npIndex)
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

    inline_ void LoadFromStream (CVolBaseInputStream& stream)
    {
        m_mem.LoadFromStream (stream);
    }

    inline_ void SaveIntoStream (CVolBaseOutputStream& stream)
    {
        m_mem.SaveIntoStream (stream);
    }

protected:
    CVolMem m_mem;
};

//-----------------------------------------------------

// POINTER_TYPE必须是指针类型
template <class POINTER_TYPE> class CMPointerArray : public CMArray<POINTER_TYPE>
{
public:
    inline_ CMPointerArray () : CMArray (32)
    {
    }

    inline_ CMPointerArray (const INT_P npAlignElementCount) :
            CMArray (npAlignElementCount)
    {
    }

public:
    inline_ void Add (const POINTER_TYPE& element)
    {
        ASSERT (sizeof (POINTER_TYPE) == sizeof (void*));  // 必须为指针数据
        m_mem.AddPointer (element);
    }

    // 返回最后一个指针成员的内容,如果数组为空则返回NULL.
    inline_ POINTER_TYPE GetLastPointer () const
    {
        return (m_mem.IsEmpty () ? NULL : GetData () [GetUpperBound ()]);
    }
};

//-----------------------------------------------------

// 支持自动/手动删除数组中所有动态对象的数组
template <class POINTER_TYPE> class CAutoDeleteObjectArray : public CMPointerArray<POINTER_TYPE>
{
public:
    inline_ CAutoDeleteObjectArray ()
    {
    }

    inline_ CAutoDeleteObjectArray (const INT_P npAlignElementCount) :
            CMPointerArray (npAlignElementCount)
    {
    }

    inline_ ~CAutoDeleteObjectArray ()
    {
        DeleteAllObjects ();
    }

public:
    // 手动删除数组中的所有动态对象
    void DeleteAllObjects ()
    {
        const INT_P npCount = GetCount ();
        const POINTER_TYPE* p = GetData ();
        for (INT_P i = 0; i < npCount; i++, p++)
        {
            if (*p != NULL)
                delete (*p);
        }

        RemoveAll ();
    }

    // 删除所指定索引位置处的动态对象
    inline_ void DeleteObject (const INT_P npIndex)
    {
        if (GetAt (npIndex) != NULL)
            delete GetAt (npIndex);
        RemoveAt (npIndex);
    }

    // 删除所指定索引位置处的一批动态对象
    inline_ void DeleteObjects (const INT_P npIndex, const INT_P npCount)
    {
        ASSERT (npIndex >= 0 && npCount >= 0 && npIndex + npCount <= GetCount ());

        if (npCount > 0)
        {
            const POINTER_TYPE* p = GetData () + npIndex;
            for (INT_P i = 0; i < npCount; i++, p++)
            {
                if (*p != NULL)
                    delete (*p);
            }

            RemoveAt (npIndex, npCount);
        }
    }

    // 删除并释放所指定的对象指针,返回该对象指针是否存在.
    inline_ BOOL_P DeleteObjectPointer (POINTER_TYPE pObject)
    {
        const INT_P npIndex = FindElement (pObject);
        if (npIndex != -1)
        {
            DeleteObject (npIndex);
            return TRUE;
        }

        return FALSE;
    }
};

//-----------------------------------------------------

// 支持自动/手动释放数组中所有动态对象的数组
template <class POINTER_TYPE> class CAutoReleaseObjectArray : public CMPointerArray<POINTER_TYPE>
{
public:
    inline_ CAutoReleaseObjectArray ()
    {
    }

    inline_ CAutoReleaseObjectArray (const INT_P npAlignElementCount) :
            CMPointerArray (npAlignElementCount)
    {
    }

    inline_ ~CAutoReleaseObjectArray ()
    {
        ReleaseAllObjects ();
    }

public:
    // 手动释放数组中的所有动态对象
    void ReleaseAllObjects ()
    {
        const INT_P npCount = GetCount ();
        const POINTER_TYPE* p = GetData ();
        for (INT_P i = 0; i < npCount; i++, p++)
            (*p)->SafeRelease ();

        RemoveAll ();
    }

    // 删除并释放所指定索引位置处的动态对象
    inline_ void ReleaseObject (const INT_P npIndex)
    {
        GetAt (npIndex)->SafeRelease ();
        RemoveAt (npIndex);
    }

    // 删除并释放所指定的对象指针,返回该对象指针是否存在.
    inline_ BOOL_P DeleteObjectPointer (POINTER_TYPE pObject)
    {
        const INT_P npIndex = FindElement (pObject);
        if (npIndex != -1)
        {
            ReleaseObject (npIndex);
            return TRUE;
        }

        return FALSE;
    }
};

//-----------------------------------------------------

#define DEFINE_MARRAY(class_name,type,add_cmd)  \
    class class_name : public CMArray<type>  \
    {  \
    public:  \
        inline_ class_name ()  {  }  \
        inline_ void Add (const type& element)  {  m_mem.add_cmd (element);  }  \
    };

DEFINE_MARRAY (CMIntArray, INT, AddInt)
DEFINE_MARRAY (CMIntPArray, INT_P, AddIntP)
DEFINE_MARRAY (CMDWordArray, DWORD, AddDWord)
DEFINE_MARRAY (CMUIntPArray, UINT_P, AddUIntP)
DEFINE_MARRAY (CMInt64Array, INT64, AddInt64)
DEFINE_MARRAY (CMUInt64Array, UINT64, AddUInt64)
DEFINE_MARRAY (CMFloatArray, FLOAT, AddFloat)
DEFINE_MARRAY (CMDoubleArray, DOUBLE, AddDouble)
DEFINE_MARRAY (CMBoolPArray, BOOL_P, AddBoolP)

typedef CMPointerArray<void*> CMVoidPtrArray;

//--------------------------------------------------------------------------------------

// 火山对象管理数组
class CVolObjectArray : public CVolObject
{
    DECLARE_GLOBAL_VOL_CLASS (CVolObjectArray)

public:
    inline_ CVolObjectArray (const INT_P npAlignElementCount = 32)
    {
        SetAlignElementCount (npAlignElementCount);
    }

    virtual ~CVolObjectArray ()
    {
        RemoveAll ();
    }

    inline_ void SetAlignElementCount (const INT_P npAlignElementCount)
    {
        ASSERT (npAlignElementCount >= 0);
        m_arypObjects.SetAlignElementCount (npAlignElementCount);
    }
    inline_ INT_P GetAlignElementCount () const
    {
        return m_arypObjects.GetAlignElementCount ();
    }

    inline_ INT_P GetCount () const
    {
        return m_arypObjects.GetCount ();
    }

    inline_ INT_P GetUpperBound () const
    {
        return m_arypObjects.GetUpperBound ();
    }

    // 返回指定索引值是否在本数组内有效
    inline_ BOOL_P IsIndexValid (const INT_P npIndex) const
    {
        return m_arypObjects.IsIndexValid (npIndex);
    }

    inline_ BOOL_P IsEmpty () const
    {
        return m_arypObjects.IsEmpty ();
    }

    void RemoveAll ();

    inline_ CVolObject& GetAt (const INT_P npIndex)
    {
        return *m_arypObjects.GetAt (npIndex);
    }

    inline_ CVolObject* GetPtrAt (const INT_P npIndex)
    {
        return m_arypObjects.GetAt (npIndex);
    }

    inline_ CVolObject& GetAt (const INT_P npIndex, const CVolRuntimeClass* pRuntimeClass, CVolObject& objDummy)
    {
        ASSERT (pRuntimeClass != NULL && objDummy.IsVolInstanceOf (pRuntimeClass));
        CVolObject& obj = *m_arypObjects.GetAt (npIndex);
        return (obj.IsVolInstanceOf (pRuntimeClass) ? obj : objDummy.SetNullObjectFlag ());
    }

    inline_ CVolObject& operator[] (const INT_P npIndex)
    {
        return *m_arypObjects.GetAt (npIndex);
    }

    inline_ void XchgElement (const INT_P npIndex1, const INT_P npIndex2)
    {
        m_arypObjects.XchgElement (npIndex1, npIndex2);
    }

    void Append (const CVolObjectArray& src);

    void RemoveAt (const INT_P npIndex, const INT_P npCount = 1);
    void SetAt (const INT_P npIndex, const CVolObject& obj);

    INT_P Add (const CVolObject& obj, CVolObject** ppNewVolObject);
    INT_P AddNewObject (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue);
    CVolObject& AddNewObject (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue, INT* pnElementIndex);
    INT_P AddNewObjects (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue, const INT_P npNumNewObjects);
    INT_P AddTakeOverObject (CVolObject* pVolObject);

    inline_ void InitCount (const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue, const INT_P npNumNewObjects)
    {
        RemoveAll ();
        AddNewObjects (pRuntimeClass, npUserValue, npNumNewObjects);
    }

    CVolObject& InsertAt (const INT_P npIndex, const CVolObject& obj);
    CVolObject& InsertNewObject (const INT_P npIndex, const CVolRuntimeClass* pRuntimeClass, const INT_P npUserValue);

    inline_ BOOL_P IsElementInstanceOf (const INT_P npIndex, const CVolRuntimeClass* pRuntimeClass)
    {
        ASSERT (IsIndexValid (npIndex));
        ASSERT_R_DATA (pRuntimeClass);
        return m_arypObjects.GetAt (npIndex)->IsVolInstanceOf (pRuntimeClass);
    }

    inline_ BOOL_P IsElementClass (const INT_P npIndex, const CVolRuntimeClass* pRuntimeClass)
    {
        ASSERT (IsIndexValid (npIndex));
        ASSERT_R_DATA (pRuntimeClass);
        return m_arypObjects.GetAt (npIndex)->IsVolClass (pRuntimeClass);
    }

    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override;

protected:
    CMPointerArray<CVolObject*> m_arypObjects;
};

#endif
