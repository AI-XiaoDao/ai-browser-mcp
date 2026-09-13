
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_SORT_ARRAY_H__
#define __VOL_SORT_ARRAY_H__

// 自动排序的数组
template <class T> class CSortArray : public CVolCommonBase
{
public:
    inline_ CSortArray ()
    {
        SetAlignElementCount (32);
    }

    inline_ CSortArray (const INT_P npAlignElementCount)
    {
        SetAlignElementCount (npAlignElementCount);
    }

    inline_ void SetAlignElementCount (const INT_P npAlignElementCount)
    {
        m_mem.SetMemAlignSize (npAlignElementCount * sizeof (T));
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

    inline_ void Empty ()
    {
        m_mem.Empty ();
    }

    inline_ void RemoveAt (const INT_P npIndex, const INT_P npCount = 1)
    {
        ASSERT (npIndex >= 0 && npIndex + npCount <= GetCount ());
        m_mem.Remove (npIndex * sizeof (T), sizeof (T) * npCount);
    }

    inline_ void RemoveToEnd (const INT_P npBeginIndex)
    {
        ASSERT (npBeginIndex >= 0);
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

    inline_ T* GetElementData (const INT_P npIndex)
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return GetData () + npIndex;
    }

    inline_ const T* GetElementData (const INT_P npIndex) const
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return GetData () + npIndex;
    }

    inline_ const T& GetAt (const INT_P npIndex) const
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return GetData () [npIndex];
    }

    inline_ T& GetAt (const INT_P npIndex)
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return GetData () [npIndex];
    }

    inline_ const T& operator[] (const INT_P npIndex) const
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return GetData () [npIndex];
    }

    inline_ T& operator[] (const INT_P npIndex)
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return GetData () [npIndex];
    }

    inline_ void Copy (const CSortArray<T>& src)
    {
        m_mem.CopyFrom (src.m_mem);
    }

    inline_ CVolMem& GetMem ()
    {
        return m_mem;
    }
    inline_ const CVolMem& GetMem () const
    {
        return m_mem;
    }

    inline_ BOOL_P IsEqual (const INT_P npIndex, const T& data) const
    {
        ASSERT (npIndex >= 0 && npIndex < GetCount ());
        return (compare (*GetElementData (npIndex), data) == 0);
    }

    inline_ BOOL_P IsEqual (const CSortArray<T>& ary) const
    {
        const INT_P npDataSize = GetDataSize ();
        if (ary.GetDataSize () != npDataSize)
            return FALSE;

        return (memcmp (GetData (), ary.GetData (), npDataSize) == 0);
    }

    inline_ BOOL_P IsEqual (const T* pElementData, const INT_P npNumElements) const
    {
        ASSERT_R_ADR (pElementData, sizeof (T) * npNumElements);

        if (GetCount () != npNumElements)
            return FALSE;

        return (memcmp (GetData (), pElementData, npNumElements * sizeof (T)) == 0);
    }

    // 将指定数据加入数组,返回所加入位置的索引.
    // 注意! 此加入成员的索引位置不是固定的,其很可能会被后续成员加入操作更改.
    virtual INT_P Add (const T& data)
    {
        return Add (data, FALSE);
    }

    // 将指定数据加入数组,返回所加入位置的索引.
    // 如果存在同等成员且blpAddAtEnd参数为真,则加在同等成员的尾部.
    // 注意! 此加入成员的索引位置不是固定的,其很可能会被后续成员加入操作更改.
    virtual INT_P Add (const T& data, const BOOL_P blpAddAtEnd)
    {
        const T* ary = (const T*)m_mem.GetPtr ();
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

        m_mem.Insert (npLowIndex * sizeof (T), &data, sizeof (T));
        return npLowIndex;
    }

    // 寻找指定成员,找到返回其索引位置,否则返回-1. 
    // 注意: 1.所找到的可能并非第一个等于该值的成员; 2.数组必须处于完全排序状态
    INT_P FindElement (const T& data) const
    {
        const T* ary = (const T*)m_mem.GetPtr ();
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

    inline_ BOOL_P IsElementExist (const T& data) const
    {
        return (FindElement (data) != -1);
    }

    // 返回第一个等于指定数据的成员的索引位置,如果没找到则返回-1. 
    // 注意: 数组必须处于完全排序状态
    INT_P FindFirstElement (const T& data) const
    {
        INT_P npIndex = FindElement (data);
        if (npIndex == -1)
            return -1;

        npIndex--;

        const T* ary = (const T*)m_mem.GetPtr ();
        while (npIndex >= 0)
        {
            if (compare (data, ary [npIndex]) != 0)
                break;
            npIndex--;
        }

        return npIndex + 1;
    }

    // 返回最后一个等于指定数据的成员的索引位置,如果没找到则返回-1. 
    // 注意: 数组必须处于完全排序状态
    INT_P FindLastElement (const T& data) const
    {
        INT_P npIndex = FindElement (data);
        if (npIndex == -1)
            return -1;

        npIndex++;

        const T* ary = (const T*)m_mem.GetPtr ();
        const INT_P npCount = GetCount ();
        while (npIndex < npCount)
        {
            if (compare (data, ary [npIndex]) != 0)
                break;
            npIndex++;
        }

        return npIndex - 1;
    }

    // 寻找本成员小于或等于data但其下一成员大于data的数组成员的索引位值,未找到则返回-1. 
    // npBeginIndex和npEndIndex提供在数组内的搜寻起始结束范围. npEndIndex为-1表示数组尾部. 
    // 注意: 数组必须处于完全排序状态
    INT_P FindInside (const T& data, const INT_P npBeginIndex = 0, const INT_P npEndIndex = -1) const
    {
        if (npEndIndex == -1)
            npEndIndex = GetCount () - 1;

        ASSERT (npBeginIndex >= 0 && npBeginIndex < GetCount () &&
                npEndIndex >= 0 && npEndIndex < GetCount ());
        if (npEndIndex <= npBeginIndex)
            return -1;

        //-----------------------------------

        INT_P npLowIndex = npBeginIndex;
        INT_P npHighIndex = npEndIndex;

        const T* ary = (const T*)m_mem.GetPtr ();
        while (npLowIndex <= npHighIndex)
        {
            const INT_P npMidIndex = (npHighIndex + npLowIndex) / 2;

            if (compare (ary [npMidIndex], data) > 0)  // npMidIndex成员大于data?
            {
                npHighIndex = npMidIndex - 1;
            }
            // 如果npMidIndex成员小于等于data且其下一成员大于data,则返回搜寻成功. 
            else if (npMidIndex < npEndIndex && compare (ary [npMidIndex + 1], data) > 0)
            {
                return npMidIndex;
            }
            else
                npLowIndex = npMidIndex + 1;
        }

        return -1;
    }

    // 直接寻找所指定的成员
    INT_P DirectFindElement (const T& data) const
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

    // 返回指定指针是否处在本数组对象的尾部
    inline_ BOOL_P IsAtEnd (const void* p) const
    {
        return m_mem.IsAtEnd (p);
    }

    //-------------------------------------------------------
    // 非自动排序操作,调用完毕后需要使用Sort方法手工排序

    inline_ T* InitCount (const INT_P npNumElements, const BOOL_P blpZero)
    {
        ASSERT (npNumElements >= 0);

        T* pElement = (T*)m_mem.Alloc (npNumElements * sizeof (T));
        if (blpZero)
            ZERO_MEM (pElement, npNumElements * sizeof (T));
        return pElement;
    }

    inline_ T* AddEmptyElements_NotSort (const INT_P npNumElements, const BOOL_P blpZero = FALSE)
    {
        ASSERT (npNumElements >= 0);
        return (T*)m_mem.AddSpace (npNumElements * sizeof (T), blpZero);
    }

    inline_ void Add_NotSort (const T& data)
    {
        m_mem.Append (&data, sizeof (T));
    }

    inline_ void Append_NotSort (const T* pElements, const INT_P npCount)
    {
        m_mem.Append (pElements, sizeof (T) * npCount);
    }

    inline_ void Append_NotSort (const CSortArray<T>& ary)
    {
        m_mem.Append (ary.m_mem);
    }

    inline_ void Copy_NotSort (const T* pElements, const INT_P npCount)
    {
        m_mem.CopyFrom (pElements, sizeof (T) * npCount);
    }

    void Sort ()  // 希尔排序法
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

    //-------------------------------------------------------

    friend inline_ CVolBaseOutputStream& operator<< (CVolBaseOutputStream& stream, const CSortArray<T>& ary)
    {
        stream << ary.m_mem;
        return stream;
    }

    friend inline_ CVolBaseInputStream& operator>> (CVolBaseInputStream& stream, CSortArray<T>& ary)
    {
        stream >> ary.m_mem;
        return stream;
    }

protected:
    virtual INT_P compare (const T& element1, const T& element2) const = 0;

protected:
    CVolMem m_mem;  // 记录所有成员值的有序数组
};

//---------------------------------------------------------------------

// 用作保存数值等可以直接进行值比较的数据成员的数组
template <class T> class CNumSortArray : public CSortArray<T>
{
public:
    inline_ CNumSortArray ()
    {
    }

    inline_ CNumSortArray (const INT_P npAlignElementCount) :
            CSortArray<T> (npAlignElementCount)
    {
    }

protected:
    virtual INT_P compare (const T& element1, const T& element2) const override
    {
        return (element1 > element2) ? 1 :
                (element1 < element2) ? -1 :
                0;
    }
};

typedef CNumSortArray<void*> CPtrSortArray;  // 指针排序数组

#endif
