
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_COM_H__
#define __VOL_COM_H__

#include <olectl.h>

extern const IID IID_IVolComRecordObject;

MIDL_INTERFACE ("8AB1733C-F55B-4347-A61C-B257280F9967")
IVolComObject : public IUnknown
{
    virtual CVolObject* STDMETHODCALLTYPE GetVolObject (void) = 0;
    virtual void STDMETHODCALLTYPE TakeOverVolObject (CVolObject* pVolObject) = 0;
};

class CVolComRecordObject : public IVolComObject
{
public:
    inline_ CVolComRecordObject ()
    {
        m_lRefCount = 1;
        m_pVolObject = NULL;
    }

    virtual ~CVolComRecordObject ()
    {
        if (m_pVolObject != NULL)
            m_pVolObject->Destroy ();
    }

public:
    virtual HRESULT STDMETHODCALLTYPE QueryInterface (REFIID riid, void** ppvObject) override;
    virtual ULONG STDMETHODCALLTYPE AddRef (void) override;
    virtual ULONG STDMETHODCALLTYPE Release (void) override;

    virtual CVolObject* STDMETHODCALLTYPE GetVolObject (void) override
    {
        return m_pVolObject;
    }

    virtual void STDMETHODCALLTYPE TakeOverVolObject (CVolObject* pVolObject) override;

    static CVolObject* sGetVolObject (IUnknown* punkVal);
    static CVolObject& sGetVolObject (IUnknown* punkVal, CVolRuntimeClass* pRuntimeClass, CVolObjectDestroyer& objDestroyer);
    static CVolComRecordObject* sCreateNew (CVolObject* pVoldObjectCopyFrom);

private:
    LONG m_lRefCount;
    CVolObject* m_pVolObject;
};

//------------------------------------------------------------------------------------------------

typedef enum
{
    VVT_UNKNOWN = -1,

    VVT_EMPTY,
    VVT_ERROR,
    VVT_SBYTE,
    VVT_SHORT,
    VVT_INT,
    VVT_LONG,
    VVT_FLOAT,
    VVT_DOUBLE,
    VVT_DATE,
    VVT_BOOL,
    VVT_STR,
    VVT_COM_OBJECT,
    VVT_COM_DISPATCH,

    VVT_ERROR_ARRAY,
    VVT_SBYTE_ARRAY,
    VVT_SHORT_ARRAY,
    VVT_INT_ARRAY,
    VVT_LONG_ARRAY,
    VVT_FLOAT_ARRAY,
    VVT_DOUBLE_ARRAY,
    VVT_DATE_ARRAY,
    VVT_BOOL_ARRAY,
    VVT_STR_ARRAY,
    VVT_COM_OBJECT_ARRAY,
    VVT_COM_DISPATCH_ARRAY,
    VVT_VARIANT_ARRAY,

    _NUM_VOL_VARIANT_TYPES
}
VOL_VARIANT_TYPE;

typedef enum
{
    VNET_ERROR = 0,
    VNET_SBYTE,
    VNET_SHORT,
    VNET_INT,
    VNET_LONG,
    VNET_FLOAT,
    VNET_DOUBLE,
    VNET_DATE,
    VNET_BOOL,
    VNET_STR,
    VNET_COM_OBJECT,
    VNET_COM_DISPATCH,
    VNET_VARIANT,

    _NUM_VOL_NEW_VARY_ELEMENT_TYPES
}
VOL_NEW_VARY_ELEMENT_TYPE;

class CVolComObject;

class CVolComVariant : public CVolObject
{
public:
    DECLARE_GLOBAL_VOL_CLASS (CVolComVariant)

    inline_ CVolComVariant ()
    {
        init ();
    }

    ~CVolComVariant ()
    {
        ::VariantClear (&m_var);
    }

public:
    inline_ void init ()
    {
        ZERO_MEM (&m_var, sizeof (m_var));
    }

    inline_ void Clear ()
    {
        ::VariantClear (&m_var);
        init ();
    }

    inline_ BOOL_P IsEmpty () const
    {
        return (m_var.vt == VT_EMPTY);
    }

    BOOL_P IsArray () const
    {
        return ((m_var.vt & VT_ARRAY) != 0);
    }

    VOL_VARIANT_TYPE GetType () const;
    BOOL_P ChangeType (const VOL_VARIANT_TYPE enNewType);
    INT_P GetNumArrayElements () const;
    INT_P GetArrayElementSize () const;
    INT_P GetArrayDataSize () const;

    S_BYTE GetValue_S_BYTE (const INT_P npElementIndex) const;
    SHORT GetValue_SHORT (const INT_P npElementIndex) const;
    TCHAR GetValue_TCHAR (const INT_P npElementIndex) const;
    INT GetValue_INT (const INT_P npElementIndex) const;
    INT64 GetValue_INT64 (const INT_P npElementIndex) const;
    FLOAT GetValue_FLOAT (const INT_P npElementIndex) const;
    DOUBLE GetValue_DOUBLE (const INT_P npElementIndex) const;
    BOOL GetValue_BOOL (const INT_P npElementIndex) const;
    CVolString GetValue_CVolString (const INT_P npElementIndex) const;
    CVolComVariant& GetRecordField (const TCHAR* szFieldName, CVolComVariant& vValue) const;

    INT_P GetArray_S_BYTE (S_BYTE* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_SHORT (SHORT* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_TCHAR (TCHAR* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_INT (INT* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_INT64 (INT64* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_FLOAT (FLOAT* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_DOUBLE (DOUBLE* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_BOOL (BOOL* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_CVolString (CVolString* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_Variant (CVolComVariant* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;
    INT_P GetArray_ComObject (CVolComObject* pBuf, const INT_P npMaxNumBufElements, INT_P npFirstReadElementIndex, INT_P npNumReadElements) const;

    CVolObject& GetVolObject (const INT_P npElementIndex, CVolRuntimeClass* pRuntimeClass, CVolObjectDestroyer& objDestroyer) const;
    BOOL_P GetBin (CVolMem* pVolMem);
    BOOL_P GetComObject (CVolComObject* pVolComObject, const INT_P npElementIndex);
    CVolComObject& GetComObject2 (CVolComObject& objVolCom, const INT_P npElementIndex);

    BOOL_P Set_S_BYTE (const S_BYTE value, const INT_P npElementIndex);
    BOOL_P Set_SHORT (const SHORT value, const INT_P npElementIndex);
    BOOL_P Set_TCHAR (const TCHAR value, const INT_P npElementIndex);
    BOOL_P Set_INT (const INT value, const INT_P npElementIndex);
    BOOL_P Set_INT64 (const INT64 value, const INT_P npElementIndex);
    BOOL_P Set_FLOAT (const FLOAT value, const INT_P npElementIndex);
    BOOL_P Set_DOUBLE (const DOUBLE value, const INT_P npElementIndex);
    BOOL_P Set_BOOL (const BOOL value, const INT_P npElementIndex);
    BOOL_P Set_CVolString (const TCHAR* value, const INT_P npElementIndex);
    BOOL_P SetComObject (IUnknown* pComObject, const INT_P npElementIndex);
    BOOL_P SetComDispatchObject (IUnknown* pComObject, const INT_P npElementIndex);
    BOOL_P SetVolObject (CVolObject* pVolObject, const INT_P npElementIndex);
    BOOL_P SetVariant (const VARIANT* pVar, const INT_P npElementIndex);

    BOOL_P CreateArray_S_BYTE (const S_BYTE* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_SHORT (const SHORT* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_TCHAR (const TCHAR* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_INT (const INT* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_INT64 (const INT64* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_FLOAT (const FLOAT* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_DOUBLE (const DOUBLE* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_BOOL (const BOOL* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_CVolString (const CVolString* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_Variant (const CVolComVariant* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_ComObject (const CVolComObject* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateArray_ComDispatchObject (const CVolComObject* pData, const INT_P npMaxNumElements, INT_P npFirstWriteElementIndex, INT_P npNumWriteElements);
    BOOL_P CreateByteArrayFromData (const void* pData, const INT_P npDataSize);

    inline_ BOOL_P CreateArrayFromBin (const CVolMem* pVolMem)
    {
        ASSERT (pVolMem != NULL);
        return CreateByteArrayFromData (pVolMem->GetPtr (), pVolMem->GetSize ());
    }

    BOOL_P CreateEmptyArray (const VOL_NEW_VARY_ELEMENT_TYPE enType, const INT_P npNumElements);
    BYTE* LockArray ();
    void UnlockArray ();

    BOOL_P GetValue (const INT_P npElementIndex, const VARTYPE vtReq, VARIANT* pvarRes) const;
    INT_P GetArray (void* pBuf, INT_P npNumReadElements, INT_P npFirstReadElementIndex, const INT_P npElementSize) const;
    BOOL_P SetValue (VARIANT* pvarNew, const INT_P npElementIndex);
    BOOL_P CreateArray (const VOL_NEW_VARY_ELEMENT_TYPE enType, const void* pData, const INT_P npNumElements, const INT_P npElementSize);

    inline_ SAFEARRAY* GetSafeArray () const
    {
        return ((m_var.vt & VT_ARRAY) == 0 ? NULL :
                ((m_var.vt & VT_BYREF) != 0 ? *m_var.pparray : m_var.parray));
    }

    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override;

public:
    VARIANT m_var;
};

//------------------------------------------------------------------------------------------------

class CVolComObject : public CVolObject
{
public:
    DECLARE_GLOBAL_VOL_CLASS (CVolComObject)

    inline_ CVolComObject ()
    {
        m_pUnknownObject = NULL;
        m_enInvokeResult = IRT_SUCCEEDED;
    }

    ~CVolComObject ()
    {
        if (m_pUnknownObject != NULL)
            m_pUnknownObject->Release ();
    }

public:
    inline_ BOOL_P IsEmpty () const
    {
        return (m_pUnknownObject == NULL);
    }

    void ReleaseUnknownObject ();
    void SetUnknownObject (IUnknown* pUnknownObject);
    void TakeOverNewUnknownObject (IUnknown* pNewUnknownObject);
    IUnknown* GetUnknownObject ()  {  return m_pUnknownObject;  }

    BOOL_P CreateComObject (const TCHAR* szObjectTypeName, const TCHAR* szTypeLibFileName);
    BOOL_P QueryComObject (const TCHAR* szObjectTypeName);
    BOOL_P QueryComInterface (const TCHAR* szInterfaceName, CVolComObject& objResult);
    CVolComObject& QueryComInterface2 (const TCHAR* szInterfaceName, CVolComObject& objResult);
    BOOL_P CreatePicDispObject (const HBITMAP hBitmap);
    BOOL_P GetPicDispData (CVolMem& memResult);
    BOOL_P CreateFontDispObject (const HFONT hFont);
    HFONT CreateFontFromDispData ();
    BOOL_P CreateFontDispObjectFromInfo (const LOGFONT* pinfFont);

    typedef enum
    {
        IMT_GET_PROPERTY = 0,
        IMT_SET_PROPERTY,
        IMT_RUN_METHOD
    }
    INVOKE_METHOD_TYPE;

    S_BYTE Invoke_S_BYTE (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    SHORT Invoke_SHORT (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    TCHAR Invoke_TCHAR (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    INT Invoke_INT (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    INT64 Invoke_INT64 (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    FLOAT Invoke_FLOAT (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    DOUBLE Invoke_DOUBLE (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    BOOL Invoke_BOOL (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    CVolString Invoke_CVolString (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    CVolComVariant Invoke_CVolComVariant (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    CVolComObject Invoke_CVolComObject (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    CVolComObject& Invoke_ComObject (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, CVolComObject& objResult, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);
    BOOL_P Invoke (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, ...);

    static BOOL_P sGetClassIDFromString (const TCHAR* szObjectTypeName, CLSID* pClsID);
    static BOOL_P sRegOcx (const TCHAR* szOCXFileName, const BOOL_P blpRegister);

protected:
    typedef enum
    {
        ICPT_EMPTY = 0,

        ICPT_SBYTE,   // 字节
        ICPT_SHORT,   // 短整数
        ICPT_WCHAR,   // 字符
        ICPT_INT,     // 整数
        ICPT_VINT,    // 变整数
        ICPT_LONG,    // 长整数
        ICPT_FLOAT,   // 单精度小数
        ICPT_DOUBLE,  // 小数
        ICPT_BOOL,    // 逻辑型

        _ICPT_REF_PARAM_TYPE_BEGIN,
            ICPT_P_SBYTE = _ICPT_REF_PARAM_TYPE_BEGIN,   // 字节指针
            ICPT_P_SHORT,   // 短整数指针
            ICPT_P_WCHAR,   // 字符指针
            ICPT_P_INT,     // 整数指针
            ICPT_P_VINT,    // 变整数指针
            ICPT_P_LONG,    // 长整数指针
            ICPT_P_FLOAT,   // 单精度小数指针
            ICPT_P_DOUBLE,  // 小数指针
            ICPT_P_BOOL,    // 逻辑型指针

            ICPT_P_STRING,  // 文本型指针
            ICPT_P_COM_VARIANT,  // COM变体型指针
            ICPT_P_COM_OBJECT,  // COM对象类指针
        _ICPT_DUMMY1,
        _ICPT_REF_PARAM_TYPE_END = _ICPT_DUMMY1 - 1,

        _NUM_INVOKE_PARAM_TYPES
    }
    INVOKE_CALL_PARAM_TYPE;
    #define IS_POINTER_CALL_PARAM(enType)  ((enType) >= _ICPT_REF_PARAM_TYPE_BEGIN && (enType) <= _ICPT_REF_PARAM_TYPE_END)

    typedef struct
    {
        INVOKE_CALL_PARAM_TYPE m_enType;

        union
        {
            S_BYTE m_sbyte;
            SHORT m_short;
            TCHAR m_char;
            INT m_int;
            INT_P m_vint;
            INT64 m_long;
            FLOAT m_float;
            DOUBLE m_double;
            BOOL m_bool;

            S_BYTE* m_pSByte;
            SHORT* m_pShort;
            TCHAR* m_pChar;
            INT* m_pInt;
            INT_P* m_pVInt;
            INT64* m_pLong;
            FLOAT* m_pFloat;
            DOUBLE* m_pDouble;
            BOOL* m_pBool;

            CVolString* m_pStr;
            CVolComVariant* m_pVolComVariant;
            CVolComObject* m_pVolComObject;
        };
    }
    INVOKE_CALL_PARAM_DATA;
    static INT_P sParseCallParams (va_list argList, const INT_P npFirstExtendParamTypeIndex,
            const TCHAR* szParamTypes, INVOKE_CALL_PARAM_DATA** ppCallParamDataBegin, CVolMem& memResult);
    // BOOL_P ParseCallResult (const TCHAR chResultParamType, void* pResult, VARIANT* pvInvokeResult);

    // 注意pvResult必须为一个未初始化的空白VARIANT.
    BOOL_P InvokeV (const INVOKE_METHOD_TYPE enInvokeType, const TCHAR* szInvokeName, VARIANT* pvResult,
            const INT_P npFirstExtendParamTypeIndex, const TCHAR* szParamTypes, va_list argList);

    static void sDoubleToCurrency (const DOUBLE db, CY* pcy);
    static DOUBLE sCurrencyToDouble (const CY& cy);
    static VARTYPE sGetVarType (ITypeInfo* pTypeInfo, TYPEDESC* pTypeDesc);
    static BOOL sMakeRefVaiant (VARIANT* pDest, VARIANT* pSrc);
    static BOOL_P sFillRefParamResult (INVOKE_CALL_PARAM_DATA* pCallParamData, const VARIANTARG* pParamVar);

    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override;

public:
    IUnknown* m_pUnknownObject;

    typedef enum
    {
        IRT_SUCCEEDED =               0,  // 成功
        IRT_EMPTY_OBJECT =           -1,  // 对象为空
        IRT_CALLUNABLE =             -2,  // 指定对象没有调用接口
        IRT_TYPE_INFO_NOT_FOUND =    -3,  // 指定对象没有类型信息
        IRT_BAD_PARAM_COUNT =        -4,  // 参数数目错误
        IRT_BAD_VAR_TYPE =           -5,  // 无效的参数类型
        IRT_EXCEPTION =              -6,  // 发现异常
        IRT_MEMBER_NOT_FOUND =       -7,  // 未找到指定成员
        IRT_NO_NAMED_ARGS =          -8,  // 不支持命名参数
        IRT_OVERFLOW =               -9,  // 溢出
        IRT_PARAM_NOT_FOUND =       -10,  // 未找到指定参数
        IRT_TYPE_MISMATCH =         -11,  // 类型不匹配
        IRT_PARAM_NOT_OPTIONAL =    -12,  // 必需的参数数据被省略
        IRT_GET_RESULT_FAILED =     -13,  // 获取所返回结果失败
        IRT_CALL_FAILED =           -14   // 其他原因调用失败
    }
    INVOKE_RESULT_TYPE;
    INVOKE_RESULT_TYPE m_enInvokeResult;  // 执行InvokeV方法后的结果码
};

//------------------------------------------------------------------------------------------------

class CComEventHandler : IDispatch
{
public :
    CComEventHandler ();

    ~CComEventHandler ()
    {
        ShutdownConnectionPoint ();
    }

    typedef void (*PFN_ON_COM_EVENT) (CVolComObject& objEventSource, const INT dispIdMember, CVolObjectArray& aryParamVariants, CVolComVariant& vResult, UINT_P upUserData);
    inline_ void init (PFN_ON_COM_EVENT fnOnComEvent, const UINT_P upUserData)
    {
        ASSERT (fnOnComEvent != NULL);
        m_fnOnComEvent = fnOnComEvent;
        m_upUserData = upUserData;
    }

public:
    virtual HRESULT STDMETHODCALLTYPE QueryInterface (REFIID riid, void** ppvObject) override;
    virtual ULONG STDMETHODCALLTYPE AddRef (void) override;
    virtual ULONG STDMETHODCALLTYPE Release (void) override;

    virtual HRESULT STDMETHODCALLTYPE GetTypeInfoCount (UINT* pctinfo) override
    {
        return E_NOTIMPL;
    }
        
    virtual HRESULT STDMETHODCALLTYPE GetTypeInfo (UINT iTInfo, LCID lcid, ITypeInfo** ppTInfo) override
    {
        return E_NOTIMPL;
    }
        
    virtual HRESULT STDMETHODCALLTYPE GetIDsOfNames (REFIID riid, LPOLESTR* rgszNames, UINT cNames, LCID lcid, DISPID* rgDispId) override
    {
        return E_NOTIMPL;
    }

    virtual HRESULT STDMETHODCALLTYPE Invoke (DISPID dispIdMember, REFIID riid, LCID lcid, WORD wFlags, DISPPARAMS* pDispParams,
            VARIANT* pVarResult, EXCEPINFO* pExcepInfo, UINT* puArgErr) override;
	   
    inline_ BOOL_P IsEmpty () const
    {
        return (m_pUnknownObject == NULL);
    }

    BOOL_P SetupConnectionPoint (IUnknown* pUnknownObject, const TCHAR* szEventSourceInterfaceName);
    BOOL_P SetupConnectionPoint (IUnknown* pUnknownObject, REFIID riidEventSource);
    void ShutdownConnectionPoint ();
    static BOOL_P sFindDefaultEventSource (IUnknown* pUnknownObject, IID* piidDefaultEventSource);

private:
    LONG m_lRefCount;

    PFN_ON_COM_EVENT m_fnOnComEvent;
    UINT_P m_upUserData;

    IUnknown* m_pUnknownObject;
    IID m_iidEventSource;
    IConnectionPoint* m_pIConnectionPoint;
    DWORD m_dwEventCookie;
};

#endif
