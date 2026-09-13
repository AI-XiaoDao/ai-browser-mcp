
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_UNIQUE_ARRAY_H__
#define __VOL_UNIQUE_ARRAY_H__

// 只能加入唯一值的数组
template <class T> class CUniqueArray : public CSortArray<T>
{
public:
    inline_ CUniqueArray ()
    {
    }

    inline_ CUniqueArray (const INT_P npAlignElementCount) :
                CSortArray<T> (npAlignElementCount)
    {
    }

    inline_ void CopyFrom (const CSortArray<T>& ary)
    {
        RemoveAll ();
        AppendFrom (ary);
    }

    inline_ void CopyFrom (const T* pElement, const INT_P npCount)
    {
        RemoveAll ();
        AppendFrom (pElement, npCount);
    }

    inline_ void AppendFrom (const CSortArray<T>& ary)
    {
        AppendFrom (ary.GetData (), ary.GetCount ());
    }

    inline_ void AppendFrom (const T* pElement, const INT_P npCount)
    {
        ASSERT_R_ADR (pElement, sizeof (T) * npCount);

        for (INT_P npIndex = 0; npIndex < npCount; npIndex++, pElement++)
            Add (*pElement);
    }

    // 将指定数据加入数组,如果值已经存在返回-1,否则返回所加入位置的索引.
    // 注意! 此加入成员的索引位置不是固定的,其很可能会被后续成员加入操作更改.
    virtual INT_P Add (const T& data) override
    {
        return Add (data, NULL);
    }

    // 将指定数据加入数组,如果值已经存在返回-1,否则返回所加入位置的索引.
    // 如果pnpElementIndex不为NULL,则在pnpElementIndex中返回该成员的位置索引(存在返回以前的,不存在返回新加入的).
    // 注意! 此加入成员的索引位置不是固定的,其很可能会被后续成员加入操作更改.
    INT_P Add (const T& data, INT_P* pnpElementIndex)
    {
        ASSERT_RW_DATA_OR_NULL (pnpElementIndex);

        T* ary = (T*)(this->m_mem).GetPtr ();
        INT_P npLowIndex;
        INT_P npHighIndex = this->GetCount () - 1;

        if (npHighIndex < 0 ||
                this->compare (data, ary [0]) < 0)
        {
            npLowIndex = 0;
        }
        else if (this->compare (data, ary [npHighIndex]) > 0)
        {
            npLowIndex = npHighIndex + 1;
        }
        else
        {
            npLowIndex = 0;

            while (npLowIndex <= npHighIndex)
            {
                const INT_P npMidIndex = (npHighIndex + npLowIndex) / 2;
                const INT_P npCompareResult = this->compare (data, ary [npMidIndex]);

                if (npCompareResult == 0)
                {
                    if (pnpElementIndex != NULL)
                        *pnpElementIndex = npMidIndex;
                    return -1;
                }
                if (npCompareResult > 0)
                    npLowIndex = npMidIndex + 1;
                else
                    npHighIndex = npMidIndex - 1;
            }
        }

        (this->m_mem).Insert (npLowIndex * sizeof (T), &data, sizeof (T));
        if (pnpElementIndex != NULL)
            *pnpElementIndex = npLowIndex;
        return npLowIndex;
    }
};

// 只能加入唯一值的用作保存数值等可以直接进行值比较的数据成员的数组
template <class T> class CNumUniqueArray : public CUniqueArray<T>
{
public:
    inline_ CNumUniqueArray ()
    {
    }

    inline_ CNumUniqueArray (const INT_P npAlignElementCount) :
                CUniqueArray<T> (npAlignElementCount)
    {
    }

protected:
    virtual INT_P compare (const T& element1, const T& element2) const override
    {
        return ((element1 > element2) ? 1 :
                (element1 < element2) ? -1 :
                0);
    }
};

typedef CNumUniqueArray<INT>    CIntUniqueArray;
typedef CNumUniqueArray<DWORD>  CDWordUniqueArray;
typedef CNumUniqueArray<UINT64> CU64UniqueArray;
typedef CNumUniqueArray<UINT_P> CUIntPUniqueArray;
typedef CNumUniqueArray<void*>  CPtrUniqueArray;

#endif
