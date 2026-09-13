#pragma once
#ifndef FBROWSER_V8VALUE_H_
#define FBROWSER_V8VALUE_H_

#include "FBroHsBaseEvent.h"

class FBroHsV8Accessor;
class FBroHsV8Interceptor;
class FBroString;
class FBroHsV8Handler;
class FBroCefStringList;
class FBroV8ValueList;



class FBroV8Accessor :public CefV8Accessor,public FBroHsEventModel<FBroHsV8Accessor>
{
    typedef BOOL(CALLBACK* V8AccessorGet)(int, char*, HANDLE, HANDLE, HANDLE);
    typedef BOOL(CALLBACK* V8AccessorSet)(int, char*, HANDLE, HANDLE, HANDLE);

public:
    FBroV8Accessor(CefRefPtr<FBroHsV8Accessor> callback);
    FBroV8Accessor(FBroHsV8Accessor* callback);
    FBroV8Accessor(int flag, HANDLE get, HANDLE set);
    ~FBroV8Accessor();
public:
    virtual bool Get(const CefString& name,
        const CefRefPtr<CefV8Value> object,
        CefRefPtr<CefV8Value>& retval,
        CefString& exception) override;

    virtual bool Set(const CefString& name,
        const CefRefPtr<CefV8Value> object,
        const CefRefPtr<CefV8Value> value,
        CefString& exception) override;

private:
    V8AccessorGet m_Get = NULL;
    V8AccessorSet m_Set = NULL;

    int m_flag = 0;

protected:
	IMPLEMENT_REFCOUNTING(FBroV8Accessor);
};


class FBroV8Interceptor :public CefV8Interceptor,public FBroHsEventModel<FBroHsV8Interceptor>
{
    typedef BOOL(CALLBACK* V8InterceptorGet_name)(int, char*, HANDLE, HANDLE, HANDLE);
    typedef BOOL(CALLBACK* V8InterceptorGet_index)(int, int, HANDLE, HANDLE, HANDLE);
    typedef BOOL(CALLBACK* V8InterceptorSet_name)(int, char*, HANDLE, HANDLE, HANDLE);
    typedef BOOL(CALLBACK* V8InterceptorSet_index)(int, int, HANDLE, HANDLE, HANDLE);

public:
    FBroV8Interceptor(CefRefPtr<FBroHsV8Interceptor> callback);
    FBroV8Interceptor(FBroHsV8Interceptor* callback);
    FBroV8Interceptor(int flag, HANDLE Get_name, HANDLE Get_index, HANDLE Set_name, HANDLE Set_index);
    ~FBroV8Interceptor();
public:
    virtual bool Get(const CefString& name,
        const CefRefPtr<CefV8Value> object,
        CefRefPtr<CefV8Value>& retval,
        CefString& exception) override;

    virtual bool Get(int index,
        const CefRefPtr<CefV8Value> object,
        CefRefPtr<CefV8Value>& retval,
        CefString& exception) override;


    virtual bool Set(const CefString& name,
        const CefRefPtr<CefV8Value> object,
        const CefRefPtr<CefV8Value> value,
        CefString& exception) override;


    virtual bool Set(int index,
        const CefRefPtr<CefV8Value> object,
        const CefRefPtr<CefV8Value> value,
        CefString& exception)override;
private:
    V8InterceptorGet_name m_Get_name = NULL;
    V8InterceptorGet_index m_Get_index = NULL;
    V8InterceptorSet_name m_Set_name = NULL;
    V8InterceptorSet_index m_Set_index = NULL;
    int m_flag=0;

protected:
	IMPLEMENT_REFCOUNTING(FBroV8Interceptor);
};

DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateUndefined();
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateNull();
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateBool(BOOL value);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateInt(int value);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateUInt(uint32_t value);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateDouble(double value);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateDate(POINT_TIMEDATA inData);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateString(const CefString& value);
//DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateObjectStatic(FBroHsV8Accessor* accessorcallback, FBroHsV8Interceptor* interceptorcallback, int64_t& accessorflag, int64_t& interceptorflag);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateObject(CefRefPtr<FBroHsV8Accessor> accessorcallback, CefRefPtr<FBroHsV8Interceptor> interceptorcallback, int64_t& accessorflag, int64_t& interceptorflag);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateArray(int length);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateArrayBuffer(void* buffer, size_t length);

//DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateFunctionStatic(const CefString& name, FBroHsV8Handler* callback, int64_t& flag);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS  FBroHsV8Value_CreateFunction(const CefString& name, CefRefPtr<FBroHsV8Handler> callback, int64_t& flag);


/////////////////////////////////////////////后面都是类方法

DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsValid(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsUndefined(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsNull(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsBool(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsInt(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsUInt(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsDouble(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsDate(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsString(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsObject(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsArray(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsArrayBuffer(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsFunction(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsSame(CefRefPtr<CefV8Value> V8Value, CefRefPtr<CefV8Value> that);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_GetBoolValue(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT int TEXPORTS  FBroHsV8Value_GetIntValue(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT uint32_t TEXPORTS  FBroHsV8Value_GetUIntValue(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT double TEXPORTS  FBroHsV8Value_GetDoubleValue(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT time_t TEXPORTS  FBroHsV8Value_GetDateValue(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS  FBroHsV8Value_GetStringValue(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_IsUserCreated(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_HasException(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT CefRefPtr<CefV8Exception> TEXPORTS  FBroHsV8Value_GetException(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_ClearException(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_WillRethrowExceptions(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_SetRethrowExceptions(CefRefPtr<CefV8Value> V8Value, BOOL rethrow);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_HasValue_Key(CefRefPtr<CefV8Value> V8Value, const CefString& key);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_HasValue_Index(CefRefPtr<CefV8Value> V8Value, int index);
DLLEXPORT BOOL TEXPORTS  FBroHsV8Value_DeleteValue_Key(CefRefPtr<CefV8Value> V8Value, const CefString& key);
DLLEXPORT BOOL TEXPORTS FBroHsV8Value_DeleteValue_Index(CefRefPtr<CefV8Value> V8Value, int index);
DLLEXPORT CefRefPtr<CefV8Value>  TEXPORTS FBroHsV8Value_GetValue_Key(CefRefPtr<CefV8Value> V8Value, const CefString& key);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS FBroHsV8Value_GetValue_Index(CefRefPtr<CefV8Value> V8Value, int index);
DLLEXPORT BOOL TEXPORTS FBroHsV8Value_SetValue_Key(CefRefPtr<CefV8Value> V8Value, const CefString& key, CefRefPtr<CefV8Value> inObject, int inattribute);
DLLEXPORT BOOL TEXPORTS FBroHsV8Value_SetValue_index(CefRefPtr<CefV8Value> V8Value, int index, CefRefPtr<CefV8Value> inObject);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsV8Value_GetKeys(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT int TEXPORTS FBroHsV8Value_GetExternallyAllocatedMemory(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT int TEXPORTS FBroHsV8Value_AdjustExternallyAllocatedMemory(CefRefPtr<CefV8Value> V8Value, int change_in_bytes);
DLLEXPORT int TEXPORTS FBroHsV8Value_GetArrayLength(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT BOOL TEXPORTS FBroHsV8Value_NeuterArrayBuffer(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsV8Value_GetFunctionName(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT CefRefPtr<FBroHsV8Handler> TEXPORTS FBroHsV8Value_GetFunctionHandler(CefRefPtr<CefV8Value> V8Value);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS FBroHsV8Value_ExecuteFunction(CefRefPtr<CefV8Value> V8Value, CefRefPtr<CefV8Value> inObject, CefRefPtr<FBroV8ValueList> inList);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS FBroHsV8Value_ExecuteFunctionWithContext(CefRefPtr<CefV8Value> V8Value, CefRefPtr<CefV8Context> incontext, CefRefPtr<CefV8Value> inObject, CefRefPtr<FBroV8ValueList> inList);


#endif