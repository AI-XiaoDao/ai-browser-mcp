#pragma once

//安全文本
class FBroString : public virtual CefBaseRefCounted
{
public:
	virtual int WSize() = 0;
	virtual int Size() = 0;
	virtual void GetWcharData(wchar_t* retbuf) = 0;//传入指针必须预分配内存,大小通过WSize获取
	virtual void GetCharData(char* retbuf) = 0;//传入指针必须预分配内存,大小通过Size获取
	virtual void SetData(const char* indata) = 0;//只能内部使用
	virtual void SetData(const CefString& indata) = 0;//只能内部使用
	virtual CefString GetData() = 0;
};

DLLEXPORT CefRefPtr<FBroString> FBroString_Creat();
DLLEXPORT CefRefPtr<FBroString> FBroString_Creat(const CefString& value);
DLLEXPORT CefRefPtr<FBroString> FBroString_Creat(const char* value);
DLLEXPORT int FBroString_WSize(CefRefPtr<FBroString> data);
DLLEXPORT int FBroString_Size(CefRefPtr<FBroString> data);
DLLEXPORT void FBroString_GetWcharData(CefRefPtr<FBroString> data, wchar_t* retbuf);
DLLEXPORT void FBroString_GetCharData(CefRefPtr<FBroString> data, char* retbuf);
DLLEXPORT void FBroString_SetData(CefRefPtr<FBroString> data, const CefString& buf);