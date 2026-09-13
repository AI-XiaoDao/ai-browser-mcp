
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_OBJECT_H__
#define __VOL_OBJECT_H__

class CVolObject;

//--------------------------------------------------------------------------------------

// 对象的新建和删除操作基于内存池的基础类
class CVolCommonBase
{
public:
    static void* operator new (size_t size);
    static void* operator new [] (size_t size);
    static void operator delete (void* p);
    static void operator delete [] (void* p);
    static void* operator new (size_t, void* p);
};

// 基于CVolCommonBase增加了内存的管理操作支持
class CVolCommonBaseWithMemManager : public CVolCommonBase
{
public:
    //   以下方法用作基于本类所使用的内存管理对象分配和管理内存,凡是本类或其继承类中需要动态分配/管理内存时,
    // 必须使用这些方法,以避免跨模块时产生错误:

    // 分配指定尺寸内存(该尺寸可以为任意值),成功返回所分配内存指针,失败退出应用程序.
    virtual void* mgrAlloc (const INT_P npSize) const;

    // 分配指定尺寸内存(该尺寸可以为任意值),成功返回非NULL指针,失败返回NULL.
    virtual void* mgrAllocMaybeRetNull (const INT_P npSize);

    // 重分配指定尺寸内存,p必须为本对象的Alloc/Realloc方法返回值.
    // 成功返回所重分配内存指针,失败退出应用程序.
    virtual void* mgrRealloc (const void* p, const INT_P npNewSize) const;

    // 释放通过本对象所分配/重分配的内存,调用mgrAlloc所分配的内存必须调用本方法将其释放.
    virtual void mgrFree (const void* p) const;

    // 返回本类所使用的内存管理器,必定不为NULL.
    virtual void* GetMemManager () const;
};

//--------------------------------------------------------------------------------------

typedef CVolObject* (*FN_CREATE_VOL_OBJECT) ();

// 火山对象类的运行时信息类. _NAME_COMPILER_AGREED
class CVolRuntimeClass
{
public:
    inline_ CVolRuntimeClass (const U8CHAR* szClassFullName, FN_CREATE_VOL_OBJECT pfnCreateObject) :
            m_qtClassFullName (szClassFullName),
            m_pfnCreateObject (pfnCreateObject)
    {
        ASSERT_R_STR (szClassFullName);
        ASSERT (IsEmptyStr (szClassFullName) == FALSE && pfnCreateObject != NULL);
    }

    inline_ BOOL IsEqual (const CVolRuntimeClass* pinfRuntimeClass) const
    {
        ASSERT_R_DATA (pinfRuntimeClass);
        return (BOOL)(pinfRuntimeClass == this || pinfRuntimeClass->IsClassNameEqual (m_qtClassFullName));
    }

    inline_ BOOL SafeIsEqual (const CVolRuntimeClass* pinfRuntimeClass) const
    {
        if (this == NULL)
            return (pinfRuntimeClass == NULL);
        return (BOOL)(pinfRuntimeClass == this || (pinfRuntimeClass != NULL && pinfRuntimeClass->IsClassNameEqual (m_qtClassFullName)));
    }

    // szClassFullName: 所欲检查的类全名(非全局类必须包括其所处命名空间,即"命名空间::类名"格式).
    inline_ BOOL IsClassNameEqual (const U8CHAR* szClassFullName, const DWORD dwClassNameHash) const
    {
        return (BOOL)m_qtClassFullName.IsEqual (szClassFullName, dwClassNameHash);
    }
    inline_ BOOL IsClassNameEqual (const U8CHAR* szClassFullName) const
    {
        return (BOOL)m_qtClassFullName.IsEqual (szClassFullName, ::GetTextHash (szClassFullName));
    }
    inline_ BOOL IsClassNameEqual (const CQCompareConstU8Text& qtClassNameWithNameSpace) const
    {
        return (BOOL)m_qtClassFullName.IsEqual (qtClassNameWithNameSpace);
    }

    // 返回所对应类的全名称
    inline_ const U8CHAR* GetClassFullName () const
    {
        return m_qtClassFullName.GetStaticText ();
    }

    // 创建一个对应对象实例
	inline_ CVolObject* CreateObject () const
    {
        ASSERT (m_pfnCreateObject != NULL);
        return m_pfnCreateObject ();
    }

protected:
    const FN_CREATE_VOL_OBJECT m_pfnCreateObject;  // 类对象实例的创建函数指针,必定不为NULL.

    // 类名,必定为非空文本.
    // 非全局类(通过非全局类定义宏定义)必须包括其所处命名空间("命名空间::类名"格式),全局类(通过全局类定义宏定义)则直接为类名.
    const CQCompareConstU8Text m_qtClassFullName;
};

//----------------------------------------------------------------------------  内部使用的相关宏. _NAME_COMPILER_AGREED(宏中定义的相关名称)

#define _DECLARE_VOL_RUNTIME_CLASS(name_space, class_name)  \
    public:                                           \
        static CVolRuntimeClass* sGetRuntimeClass ()  \
        {                                             \
            static CVolRuntimeClass s_infRuntimeClass (#name_space "::" #class_name, class_name::sCreateNewObject);  \
            return &s_infRuntimeClass;                \
        }

#define _DECLARE_GLOBAL_VOL_RUNTIME_CLASS(class_name)  \
    public:                                            \
        static CVolRuntimeClass* sGetRuntimeClass ()   \
        {                                              \
            static CVolRuntimeClass s_infRuntimeClass (#class_name, class_name::sCreateNewObject);  \
            return &s_infRuntimeClass;                 \
        }

// 使用本宏的类必须定义一个无参数的构造方法
#define _DECLARE_VOL_CLASS_NOT_OVR_COMP(class_name)  \
    public:                                                             \
	    static CVolObject* sCreateNewObject ()                          \
        {                                                               \
            return new class_name;                                      \
        }                                                               \
        virtual const CVolRuntimeClass* GetRuntimeClass () const        \
        {                                                               \
            return sGetRuntimeClass ();                                 \
        }                                                               \
        inline_ BOOL IsVolClass (const CVolRuntimeClass* pRuntimeClass) const  \
        {                                                               \
            ASSERT_R_DATA (pRuntimeClass);                              \
            return GetRuntimeClass ()->IsEqual (pRuntimeClass);         \
        }                                                               \
        inline_ void CopyFrom (const class_name& objCopyFrom)           \
        {                                                               \
            OnBeforeDataOverwrite ();                                   \
            _CopyAll (objCopyFrom);                                     \
        }                                                               \
        inline_ class_name (const class_name& objInit) : class_name ()  \
        {                                                               \
            _CopyAll (objInit);                                         \
        }                                                               \
        inline_ class_name& operator= (const class_name& objCopyFrom)   \
        {                                                               \
            CopyFrom (objCopyFrom);                                     \
            return *this;                                               \
        }                                                               \
        virtual BOOL IsVolObjectEqual (const CVolObject& objCompare) const  \
        {                                                               \
            return (objCompare.IsVolClass (sGetRuntimeClass ()) ?       \
                    IsEqual ((class_name&)objCompare) : FALSE);         \
        }                                                               \
        virtual CVolObject* CreateNewObject () const                    \
        {                                                               \
            return new class_name;                                      \
        }                                                               \
        virtual CVolObject* MakeCloneObject () const                    \
        {                                                               \
            return new class_name (*this);                              \
        }                                                               \
        virtual BOOL CheckCopyFrom (const CVolObject& objCopyFrom)      \
        {                                                               \
            if (objCopyFrom.IsVolInstanceOf (sGetRuntimeClass ()))      \
            {                                                           \
                CopyFrom ((class_name&)objCopyFrom);                    \
                return TRUE;                                            \
            }                                                           \
            return FALSE;                                               \
        }                                                               \
        virtual void ResetObject ()                                     \
        {                                                               \
            CopyFrom (class_name ());                                   \
        }

#define _DECLARE_VOL_CLASS_COMPARE_OPERATOR(class_name)  \
    public:                                              \
        inline_ friend static BOOL_P operator== (const class_name& obj1, const class_name& obj2)  \
        {                                                             \
            return (&obj1 == &obj2);                                  \
        }                                                             \
        inline_ friend static BOOL_P operator!= (const class_name& obj1, const class_name& obj2)  \
        {                                                             \
            return (&obj1 != &obj2);                                  \
        }

// 使用本宏的类必须实现以下方法(已经被定义):
// 1. 用作从另外一个本类对象复制内容,注意不需要复制基础类对象的内容:
//     void _CopySelfFrom (const class_name& objCopyFrom);
//         objCopyFrom: 所欲复制内容的来源对象
// 2. 用作和另外一个本类对象对比内容是否相同,注意不需要对比基础类对象的内容
//     BOOL _IsSelfEqual (const class_name& objCompare) const;
//         objCompare: 所欲对比内容的对象
#define _DECLARE_NOT_EMPTY_VOL_CLASS_CONTENT(class_name)  \
    protected:                                                     \
        BOOL _IsSelfEqual (const class_name& objCompare) const;    \
        void _CopySelfFrom (const class_name& objCopyFrom);        \
        inline_ void _CopyAll (const class_name& objCopyFrom)      \
        {                                                          \
            BaseClass::_CopyAll (objCopyFrom);                     \
            _CopySelfFrom (objCopyFrom);                           \
        }                                                          \
    public:                                                        \
        inline_ BOOL IsEqual (const class_name& objCompare) const  \
        {                                                          \
            return (BaseClass::IsEqual (objCompare) && _IsSelfEqual (objCompare));  \
        }

#define _DECLARE_VOL_CLASS_INSTANCE_OPER(class_name)  \
    public:                                 \
        typedef SelfClass BaseClass;        \
        typedef class_name SelfClass;       \
        virtual BOOL IsVolInstanceOf (const CVolRuntimeClass* pRuntimeClass) const override  \
        {                                   \
            ASSERT_R_DATA (pRuntimeClass);  \
            return (sGetRuntimeClass ()->IsEqual (pRuntimeClass) ? TRUE :  \
                    BaseClass::IsVolInstanceOf (pRuntimeClass));  \
        }

//----------------------------------------------------------------------------  非全局类定义宏

// 同DECLARE_EMPTY_VOL_CLASS(除了本宏未覆盖比较操作符)
#define DECLARE_EMPTY_VOL_CLASS_NOT_OVR_COMP(name_space, class_name)  \
        _DECLARE_VOL_RUNTIME_CLASS (name_space, class_name)  \
        _DECLARE_VOL_CLASS_INSTANCE_OPER (class_name)        \
        _DECLARE_VOL_CLASS_NOT_OVR_COMP (class_name)

// 同DECLARE_VOL_CLASS(除了本宏未覆盖比较操作符)
#define DECLARE_VOL_CLASS_NOT_OVR_COMP(name_space, class_name)  \
        DECLARE_EMPTY_VOL_CLASS_NOT_OVR_COMP (name_space, class_name)  \
        _DECLARE_NOT_EMPTY_VOL_CLASS_CONTENT (class_name)

// _NAME_COMPILER_AGREED
// 本宏在所有基于CVolObject的非空(自身存在数据成员)火山对象类中必须使用. _NAME_COMPILER_AGREED
#define DECLARE_VOL_CLASS(name_space, class_name)  \
        DECLARE_VOL_CLASS_NOT_OVR_COMP (name_space, class_name)  \
        _DECLARE_VOL_CLASS_COMPARE_OPERATOR (class_name)

// _NAME_COMPILER_AGREED
// 本宏在所有基于CVolObject的空(自身无任何数据成员)火山对象类中使用.
// 使用本宏的类必须定义一个无参数的构造方法
#define DECLARE_EMPTY_VOL_CLASS(name_space, class_name)  \
        DECLARE_EMPTY_VOL_CLASS_NOT_OVR_COMP (name_space, class_name)  \
        _DECLARE_VOL_CLASS_COMPARE_OPERATOR (class_name)

//----------------------------------------------------------------------------  全局类定义宏

// 同DECLARE_GLOBAL_EMPTY_VOL_CLASS(除了本宏未覆盖比较操作符)
#define DECLARE_GLOBAL_EMPTY_VOL_CLASS_NOT_OVR_COMP(class_name)  \
        _DECLARE_GLOBAL_VOL_RUNTIME_CLASS (class_name)  \
        _DECLARE_VOL_CLASS_INSTANCE_OPER (class_name)   \
        _DECLARE_VOL_CLASS_NOT_OVR_COMP (class_name)

// 同DECLARE_GLOBAL_VOL_CLASS(除了本宏未覆盖比较操作符)
#define DECLARE_GLOBAL_VOL_CLASS_NOT_OVR_COMP(class_name)  \
        DECLARE_GLOBAL_EMPTY_VOL_CLASS_NOT_OVR_COMP (class_name)    \
        _DECLARE_NOT_EMPTY_VOL_CLASS_CONTENT (class_name)

// 用作定义位于全局命名空间中的火山类
#define DECLARE_GLOBAL_VOL_CLASS(class_name)  \
        DECLARE_GLOBAL_VOL_CLASS_NOT_OVR_COMP (class_name)  \
        _DECLARE_VOL_CLASS_COMPARE_OPERATOR (class_name)

// 用作定义位于全局命名空间中的自身无任何成员的火山对象类
#define DECLARE_GLOBAL_EMPTY_VOL_CLASS(class_name)  \
        DECLARE_GLOBAL_EMPTY_VOL_CLASS_NOT_OVR_COMP (class_name)  \
        _DECLARE_VOL_CLASS_COMPARE_OPERATOR (class_name)

// 用作定义CVolObject类
#define _DECLARE_GLOBAL_CVOL_OBJECT_CLASS  \
        _DECLARE_GLOBAL_VOL_RUNTIME_CLASS (CVolObject)  \
        _DECLARE_VOL_CLASS_NOT_OVR_COMP (CVolObject)    \
        _DECLARE_VOL_CLASS_COMPARE_OPERATOR (CVolObject)

//----------------------------------------------------------------------------

// 返回指定对象的类是否为指定名称. _NAME_COMPILER_AGREED
#define IS_VOL_CLASS(object, class_name_with_name_space)  \
    (object).IsVolClass (class_name_with_name_space::sGetRuntimeClass ())
#define P_IS_VOL_CLASS(pobject, class_name_with_name_space)  \
    (pobject)->IsVolClass (class_name_with_name_space::sGetRuntimeClass ())

// 返回指定对象或者其基类对象的类是否为指定名称. _NAME_COMPILER_AGREED
#define IS_VOL_INSTANCE_OF(object, class_name_with_name_space)  \
    (object).IsVolInstanceOf (class_name_with_name_space::sGetRuntimeClass ())
#define P_IS_VOL_INSTANCE_OF(pobject, class_name_with_name_space)  \
    (pobject)->IsVolInstanceOf (class_name_with_name_space::sGetRuntimeClass ())

// 如果指定对象或者其基类对象的类为指定名称,则将其转换到指定类,否则返回NULL. _NAME_COMPILER_AGREED
#define P_CAST_VOL_INSTANCE(pobject, class_name_with_name_space)  \
    (P_IS_VOL_INSTANCE_OF (pobject, class_name_with_name_space) ? (class_name_with_name_space*)(pobject) : NULL)

// 相关调试宏. _NAME_COMPILER_AGREED
#ifdef _DEBUG
    #define ASSER_IS_VOL_CLASS(object, class_name_with_name_space)  ASSERT (IS_VOL_CLASS (object, class_name_with_name_space))
    #define ASSER_P_IS_VOL_CLASS(pobject, class_name_with_name_space)  ASSERT (P_IS_VOL_CLASS (pobject, class_name_with_name_space))
    #define ASSER_IS_VOL_INSTANCE_OF(object, class_name_with_name_space)  ASSERT (IS_VOL_INSTANCE_OF (object, class_name_with_name_space))
    #define ASSER_P_IS_VOL_INSTANCE_OF(pobject, class_name_with_name_space)  ASSERT (P_IS_VOL_INSTANCE_OF (pobject, class_name_with_name_space))
#else
    #define ASSER_IS_VOL_CLASS(object, class_name_with_name_space)
    #define ASSER_P_IS_VOL_CLASS(pobject, class_name_with_name_space)
    #define ASSER_IS_VOL_INSTANCE_OF(object, class_name_with_name_space)
    #define ASSER_P_IS_VOL_INSTANCE_OF(pobject, class_name_with_name_space)
#endif

// 获得指定火山类的运行时类
#define VOL_RUNTIME_CLASS(vol_class_name)  vol_class_name::sGetRuntimeClass ()

#define _VOL_THIS  (*this)  // 本对象
#define _VOL_SUPER (*(BaseClass*)this)  // 父对象

//----------------------------------------------------------------------------

class CVolString;
class CVolBaseInputStream;
class CVolBaseOutputStream;

// 用作记录火山程序对象的版本号
#define _VOL_OBJECT_VERSION_0  0  // 注意必须从0开始以兼容以前
// 用作记录火山程序对象的当前版本号
#define CURRENT_VOL_OBJECT_VERSION  _VOL_OBJECT_VERSION_0

// 所有火山程序对象的基础类
class _NAME_COMPILER_AGREED (CVolObject) : public CVolCommonBaseWithMemManager
{
    _DECLARE_GLOBAL_CVOL_OBJECT_CLASS

public: 
    inline_ CVolObject ()
    {
        m_upSysFlags = (CURRENT_VOL_OBJECT_VERSION << 24);
        m_npUserValue = 0;
    }

    virtual ~CVolObject ()
    {
    }

    virtual void _NAME_COMPILER_AGREED (Destroy) ()
    {
        delete this;
    }

    inline_ void _NAME_COMPILER_AGREED (SafeDestroy) ()
    {
        if (this != NULL)
            Destroy ();
    }

    // 返回所指定对象是否与本对象基于同一个内存管理器
    inline_ BOOL IsBaseSameMemManager (const CVolObject* pObject) const
    {
        ASSERT_R_DATA (pObject);
        return (GetMemManager () == pObject->GetMemManager ());
    }

    typedef CVolObject SelfClass;  // _NAME_COMPILER_AGREED

public: 
    #define VOSF_NULL_OBJECT                (1 << 0)  // "空白对象"标志,用作标记本对象是否为一个空对象.
    #define _VOSF_ON_BEFORE_OBJECT_CLEANUP  (1 << 1)  // OnBeforeObjectCleanup是否已经被调用(内部使用)
    UINT_P m_upSysFlags;  // 用作保存对象的相关系统标志以及对象版本

    INT_P m_npUserValue;  // 保存一个用户自定义整数值

public: 
    virtual BOOL IsVolInstanceOf (const CVolRuntimeClass* pRuntimeClass) const
    {
        return sGetRuntimeClass ()->IsEqual (pRuntimeClass);
    }

    //---------- 注意(Inner): 以下虚拟方法的格式如果发生改变,必须同步修改部件DLL的编译代码.

    // 将本对象中的所有数据用文本方式填入到strDump中,用作调试或其它场合展示时使用.
    // 注意方法名不可更改,否则会导致类库中的"增强对象类.取展示内容"方法覆盖失败.
    //   nMaxDumpSize: 提供用户所指定的最大允许展示数据尺寸,小于0表示全部展示,等于0表示展示默认尺寸数据.
    virtual void _NAME_COMPILER_AGREED (GetDumpString) (CVolString& strDump, INT nMaxDumpSize);

    // 流操作
    virtual void _NAME_COMPILER_AGREED (LoadFromStream) (CVolBaseInputStream& stream)  { }
    virtual void _NAME_COMPILER_AGREED (SaveIntoStream) (CVolBaseOutputStream& stream) { }

    //-----------------------------------------------------------------------------

    // 返回本对象是否设置了"空白对象"标志
    inline_ BOOL_P IsNullObject () const
    {
        return ((m_upSysFlags & VOSF_NULL_OBJECT) != 0);
    }

    inline_ CVolBaseInputStream& VolLoadFromStream (CVolBaseInputStream& stream)
    {
        LoadFromStream (stream);
        return stream;
    }

    inline_ CVolBaseOutputStream& VolSaveIntoStream (CVolBaseOutputStream& stream) const
    {
        ((CVolObject*)this)->SaveIntoStream (stream);
        return stream;
    }

    // 返回本对象是否未设置"空白对象"标志
    inline_ BOOL_P IsNotNullObject () const
    {
        return ((m_upSysFlags & VOSF_NULL_OBJECT) == 0);
    }
    
    // 设置本对象的"空白对象"标志,然后返回本对象.
    // 注意: 本方法仅供 _NULL_VOL_OBJECT 宏使用,其它情况下不要调用本方法(应该调用ResetToNullObject),因为其没有清空对象内容.
    inline_ CVolObject& SetNullObjectFlag ()
    {
        m_upSysFlags |= VOSF_NULL_OBJECT;
        return *this;
    }

    // 重置本对象的内容到初始状态,并设置"空白对象"标志.
    inline_ void ResetToNullObject ()
    {
        ResetObject ();
        m_upSysFlags |= VOSF_NULL_OBJECT;
    }

    // 清除本对象的"空白对象"标志.
    inline_ void RemoveNullObjectFlag ()
    {
        m_upSysFlags &= ~VOSF_NULL_OBJECT;
    }

    inline_ BOOL IsEqual (const CVolObject& objCompare) const
    {
        return (IsNullObject () == objCompare.IsNullObject () && m_npUserValue == objCompare.m_npUserValue);
    }

protected:
    inline_ void _CopyAll (const CVolObject& objCopyFrom)
    {
        m_upSysFlags = objCopyFrom.m_upSysFlags;
        m_npUserValue = objCopyFrom.m_npUserValue;
    }

    inline_ BOOL_P _NAME_COMPILER_AGREED (IsBeforeObjectCleanupNotCall) () const
    {
        return ((m_upSysFlags & _VOSF_ON_BEFORE_OBJECT_CLEANUP) == 0);
    }

    inline_ void _NAME_COMPILER_AGREED (OnBeforeObjectCleanup) ()
    {
        m_upSysFlags |= _VOSF_ON_BEFORE_OBJECT_CLEANUP;
    }

    // 在本对象的数据内容被覆盖之前,本方法被调用.
    virtual void OnBeforeDataOverwrite ()  { }
};

// 用作建立指定火山类的空对象. _NAME_COMPILER_AGREED
#define _NULL_VOL_OBJECT(class_name)  ((class_name&)class_name ().SetNullObjectFlag ())

//--------------------------------------------------------------------------------------

// 参考对象类的基础类. _NAME_COMPILER_AGREED
// 本类对象在销毁时必须调用Release方法
class CRefObject : public CVolCommonBaseWithMemManager
{
    DECLARE_BASE_CLASS (CRefObject)

public:
    inline_ CRefObject ()
    {
        m_npRefCount = 1;
    }

    virtual ~CRefObject ()
    {
        ASSERT (m_npRefCount == 1 ||  // 在堆栈上分配时
                m_npRefCount == 0);  // 采用new方法分配时
    }

public:
    inline_ void AddRef () const
    {
    #if defined (_PF_WIN32)
        _asm mov eax, [this]
        _asm lock inc dword ptr [eax + m_npRefCount]
    #elif defined (_PF_WIN64)
        _InterlockedIncrement64 ((LONGLONG*)&m_npRefCount);
    #elif defined (_PF_LINUX32)
        __asm__ __volatile__  ("lock incl %0": "=m"(m_npRefCount));
    #elif defined (_PF_LINUX64)
        __asm__ __volatile__  ("lock incq %0": "=m"(m_npRefCount));
    #else
        #error Not be supported.
    #endif
    }

    // 释放本对象的引用,如果本对象已经被实际销毁(调用本方法时对象只有一个引用),返回真,否则返回假.
    virtual BOOL Release ();

    virtual void OnBeforeDestory ()
    {
    }

    inline_ BOOL SafeRelease ()
    {
        return (this != NULL ? Release () : TRUE);
    }

    // 返回本对象现存的引用数目
    inline_ INT_P GetRefCount () const
    {
        return m_npRefCount;
    }

private:  // 以下成员必须通过成员方法访问
    mutable INT_P m_npRefCount;
};

//--------------------------------------------------------------------------------------

// 携带有数据的参考对象模板类
template<typename T> class CRefObjectWithData : public CRefObject
{
public:
    inline_ CRefObjectWithData ()
    {
        sInit (&m_data);
    }

public:
    T m_data;

protected:
    inline_ static void sInit (S_BYTE* psb)  {  *psb = 0;     }
    inline_ static void sInit (SHORT* psht)  {  *psht = 0;    }
    inline_ static void sInit (TCHAR* pch)   {  *pch = '\0';  }
    inline_ static void sInit (INT* pn)      {  *pn = 0;      }
    inline_ static void sInit (INT64* pn64)  {  *pn64 = 0;    }
    inline_ static void sInit (FLOAT* pflt)  {  *pflt = 0;    }
    inline_ static void sInit (DOUBLE* pdb)  {  *pdb = 0;     }
    inline_ static void sInit (void* pUnknown)  {  }
};

//----------------------------------------------------------------------------

// 火山对象自动释放器
class _NAME_COMPILER_AGREED (CVolObjectDestroyer) : public CVolCommonBase
{
public:
    inline_ CVolObjectDestroyer ()
    {
        m_pObject = NULL;
    }

    inline_ CVolObjectDestroyer (CVolObject* pObject)
    {
        ASSERT_R_DATA_OR_NULL (pObject);
        m_pObject = pObject;
    }

    inline_ ~CVolObjectDestroyer ()
    {
        if (m_pObject != NULL)
            m_pObject->Destroy ();
    }

    inline_ void SetVolObject (CVolObject* pObject)
    {
        ASSERT_R_DATA_OR_NULL (pObject);

        if (m_pObject != pObject)
        {
            if (m_pObject != NULL)
                m_pObject->Destroy ();
            m_pObject = pObject;
        }
    }

    // T必须是CVolObject或者其继承类
    template <class T>
    inline_ T* _NAME_COMPILER_AGREED (TSetVolObject) (T* pObject)
    {
        SetVolObject (pObject);
        return (T*)m_pObject;
    }

    inline_ CVolObject* _NAME_COMPILER_AGREED (GetVolObject) ()
    {
        return m_pObject;
    }
    inline_ CVolObject* _NAME_COMPILER_AGREED (GetVolObject) () const
    {
        return m_pObject;
    }

    inline_ void Destroy ()
    {
        if (m_pObject != NULL)
        {
            m_pObject->Destroy ();
            m_pObject = NULL;
        }
    }

    // 放弃对当前对象的释放
    inline_ void _NAME_COMPILER_AGREED (Discard) ()
    {
        m_pObject = NULL;
    }

protected:
    CVolObject* m_pObject;
};

//--------------------------------------------------------  数据指针自动删除器

template <class P> class CDataPointerDeleter : public CVolCommonBase
{
public:
    inline_ CDataPointerDeleter (P pObject = NULL)
    {
        m_pObject = pObject;
    }

    virtual ~CDataPointerDeleter ()
    {
        if (m_pObject != NULL)
            delete m_pObject;
    }

    virtual void SetObject (P pObject)
    {
        if (m_pObject != pObject)
        {
            if (m_pObject != NULL)
                delete m_pObject;
            m_pObject = pObject;
        }
    }

    virtual void Delete ()
    {
        if (m_pObject != NULL)
        {
            delete m_pObject;
            m_pObject = NULL;
        }
    }

    // 放弃对当前对象的删除,返回该对象.
    inline_ P Discard ()
    {
        P pObject = m_pObject;
        m_pObject = NULL;
        return pObject;
    }

private:
    P m_pObject;
};

//----------------------------------------------------------------------------

// 数组自动删除器
template <class T> class _NAME_COMPILER_AGREED (CArrayDeleter) : public CVolCommonBase
{
public:
    inline_ CArrayDeleter (T* pArray = NULL)
    {
        ASSERT_R_DATA_OR_NULL (pArray);
        m_pArray = pArray;
    }

    inline_ ~CArrayDeleter ()
    {
        if (m_pArray != NULL)
            delete[] m_pArray;
    }

    inline_ void SetArray (T* pArray)
    {
        ASSERT_R_DATA_OR_NULL (pArray);

        if (m_pArray != pArray)
        {
            if (m_pArray != NULL)
                delete[] m_pArray;
            m_pArray = pArray;
        }
    }

    inline_ void Delete ()
    {
        if (m_pArray != NULL)
        {
            delete[] m_pArray;
            m_pArray = NULL;
        }
    }

    // 放弃对当前数组的删除
    inline_ void Discard ()
    {
        m_pArray = NULL;
    }

private:
    T* m_pArray;
};

//----------------------------------------------------------------------------

// 用作在其中包装一个CRefObject对象
class CVolRefObject : public CVolObject
{
    DECLARE_GLOBAL_VOL_CLASS (CVolRefObject)

public:
    inline_ CVolRefObject ()
    {
        m_pRefObject = NULL;
    }

    inline_ ~CVolRefObject ()
    {
        if (m_pRefObject != NULL)
            m_pRefObject->Release ();
    }

public:
    void SetRefObject (CRefObject* pRefObject);

    // 接管一个新建的参考对象,pNewRefObject本身所具有的参考将被转移到本对象中接管.
    void TakeOverNewRefObject (CRefObject* pNewRefObject);

    inline_ CRefObject* GetRefObject ()
    {
        return m_pRefObject;
    }

protected:
    CRefObject* m_pRefObject;
};

//----------------------------------------------------------------------------

//   用作在其中包装一个任意实际数据类型的火山类对象.本类对象之间赋值时,
// 包装在本类对象中的火山对象的实际数据类型不会改变.
class CVolWrapperObject : public CVolObject
{
    DECLARE_GLOBAL_VOL_CLASS (CVolWrapperObject)

public:
    inline_ CVolWrapperObject ()
    {
        m_pRefObject = NULL;
    }

    inline_ CVolWrapperObject (CVolObject& objWrapped) : CVolWrapperObject ()
    {
        SetVolObject (objWrapped);
    }

    inline_ CVolWrapperObject (const CVolRuntimeClass* pRuntimeClass) : CVolWrapperObject ()
    {
        if (pRuntimeClass != NULL)
            CreateNewVolObject (pRuntimeClass);
    }

    ~CVolWrapperObject ()
    {
        if (m_pRefObject != NULL)
            m_pRefObject->Release ();
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return (cGetVolObjectPointer () == NULL);
    }

    inline_ void Empty ()
    {
        MSAFE_RELEASE (m_pRefObject)
    }

    CVolObject& TakeOverVolObject (CVolObject* pobjWrapped);

    inline_ CVolObject& SetVolObject (CVolObject& objWrapped)
    {
        return TakeOverVolObject (objWrapped.MakeCloneObject ());
    }

    inline_ CVolObject& CreateNewVolObject (const CVolRuntimeClass* pRuntimeClass)
    {
        ASSERT (pRuntimeClass != NULL);
        return TakeOverVolObject (pRuntimeClass->CreateObject ());
    }

    inline_ CVolObject* GetVolObjectPointer ()
    {
        return (m_pRefObject == NULL ? NULL : m_pRefObject->m_data.GetVolObject ());
    }
    inline_ CVolObject* cGetVolObjectPointer () const
    {
        return ((CVolWrapperObject*)this)->GetVolObjectPointer ();
    }

    inline_ CVolObject& GetVolObject (CVolObject& objDummy)
    {
        CVolObject* pobjWrapped = GetVolObjectPointer ();
        return (pobjWrapped == NULL ? objDummy.SetNullObjectFlag () : *pobjWrapped);
    }

    inline_ CVolObject& GetVolObject (const CVolRuntimeClass* pRuntimeClass, CVolObject& objDummy)
    {
        ASSERT (pRuntimeClass != NULL && objDummy.IsVolInstanceOf (pRuntimeClass));

        CVolObject* pobjWrapped = GetVolObjectPointer ();
        return (pobjWrapped != NULL && pobjWrapped->IsVolInstanceOf (pRuntimeClass) ? *pobjWrapped : objDummy.SetNullObjectFlag ());
    }

    inline_ BOOL_P IsVolObjectClass (const CVolRuntimeClass* pRuntimeClass) const
    {
        ASSERT (pRuntimeClass != NULL);

        CVolObject* pobjWrapped = cGetVolObjectPointer ();
        return (pobjWrapped == NULL ? FALSE : pobjWrapped->IsVolInstanceOf (pRuntimeClass));
    }

#ifdef _DEBUG
    #define _VWRP_OBJ(pRuntimeClass)  FastGetVolObject (pRuntimeClass)
    inline_ CVolObject& FastGetVolObject (const CVolRuntimeClass* pRuntimeClass)
    {
        ASSERT (IsVolObjectClass (pRuntimeClass));
        return *GetVolObjectPointer ();
    }
#else
    #define _VWRP_OBJ(pRuntimeClass)  FastGetVolObject ()
    inline_ CVolObject& FastGetVolObject ()
    {
        return *GetVolObjectPointer ();
    }
#endif

    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override;

    virtual void LoadFromStream (CVolBaseInputStream& stream) override
    {
        CVolObject* pobjWrapped = GetVolObjectPointer ();
        if (pobjWrapped != NULL)
            pobjWrapped->LoadFromStream (stream);
    }

    virtual void SaveIntoStream (CVolBaseOutputStream& stream) override
    {
        CVolObject* pobjWrapped = GetVolObjectPointer ();
        if (pobjWrapped != NULL)
            pobjWrapped->SaveIntoStream (stream);
    }

protected:
    CRefObjectWithData<CVolObjectDestroyer>* m_pRefObject;
};

#endif
