#pragma once
#ifndef FBROWSER_V8CONTEXT_H_
#define FBROWSER_V8CONTEXT_H_

#include "FBroHsBaseEvent.h"

class FBroHsV8Handler;

#ifndef _FBROELIB

//DLLEXPORT HANDLE TEXPORTS FBroHsRegisterExtensionStatic(const CefString& extension_name, const CefString& javascript_code, FBroHsV8Handler* callback);
DLLEXPORT HANDLE TEXPORTS FBroHsRegisterExtension(const CefString& extension_name, const CefString& javascript_code, CefRefPtr<FBroHsV8Handler> callback);
DLLEXPORT CefRefPtr<CefV8Context> TEXPORTS FBroHsV8Context_GetCurrentContext();
DLLEXPORT CefRefPtr<CefV8Context> TEXPORTS FBroHsV8Context_GetEnteredContext();


//下面是类方法
DLLEXPORT BOOL TEXPORTS FBroHsV8Context_InContext(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT CefRefPtr<CefTaskRunner> TEXPORTS FBroHsV8Context_GetTaskRunner(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT BOOL TEXPORTS FBroHsV8Context_IsValid(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsV8Context_GetBrowser(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT CefRefPtr<CefFrame> TEXPORTS FBroHsV8Context_GetFrame(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT CefRefPtr<CefV8Value> TEXPORTS FBroHsV8Context_GetGlobal(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT BOOL TEXPORTS FBroHsV8Context_Enter(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT BOOL TEXPORTS FBroHsV8Context_Exit(CefRefPtr<CefV8Context> V8Context);
DLLEXPORT BOOL TEXPORTS FBroHsV8Context_IsSame(CefRefPtr<CefV8Context> V8Context, CefRefPtr<CefV8Context> that);
DLLEXPORT BOOL TEXPORTS FBroHsV8Context_Eval(CefRefPtr<CefV8Context> V8Context, const CefString& code, const CefString& script_url, int start_line, CefRefPtr<CefV8Value>& retval, CefRefPtr<CefV8Exception>& exception);

//额外添加功能
DLLEXPORT void TEXPORTS FBroHsV8Context_CollectGarbage(CefRefPtr<CefV8Context> V8Context);

#endif // !_FBROELIB



typedef BOOL(CALLBACK* V8HandlerExecute)(char*, HANDLE, HANDLE, int, HANDLE, HANDLE);

class FBroV8Handler :public CefV8Handler, public FBroHsEventModel<FBroHsV8Handler>
{
public:
	FBroV8Handler(HANDLE callback);
	FBroV8Handler(CefRefPtr<FBroHsV8Handler> callback);
	FBroV8Handler(FBroHsV8Handler* callback);
	~FBroV8Handler();
public:
	virtual bool Execute(const CefString& name,
		CefRefPtr<CefV8Value> object,
		const CefV8ValueList& arguments,
		CefRefPtr<CefV8Value>& retval,
		CefString& exception) override;

protected:
	V8HandlerExecute m_callback = NULL;
protected:
	IMPLEMENT_REFCOUNTING(FBroV8Handler);
};

#endif