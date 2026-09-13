#pragma once
#ifndef FBROWSER_FRAME_H_
#define FBROWSER_FRAME_H_

#include "FBroHsBaseEvent.h"

class FBroString;
class FBroHsDOMVisitor;
class FBroHsStringVisitor;
class FBroHsJsCallback;

class FBroStringVisitor :public CefStringVisitor, public FBroHsEventModel<FBroHsStringVisitor>
{
public:
	FBroStringVisitor(int flag, HANDLE callback);
	FBroStringVisitor(CefRefPtr<FBroString> point, HANDLE inhandle);
	~FBroStringVisitor();

	FBroStringVisitor(CefRefPtr<FBroHsStringVisitor> hsvisitor);
	FBroStringVisitor(FBroHsStringVisitor* hsvisitor);

	virtual void Visit(const CefString& string) override;

private:
	int m_flag = 0;
	int m_bufsize = 0;
#ifdef _FBROELIB
	StringVisitor_callback stringvisit_callback = NULL;
#endif
	CefRefPtr<FBroString> m_fbrostring = nullptr;
	HANDLE eventhandle = NULL;

protected:
	IMPLEMENT_REFCOUNTING(FBroStringVisitor);

};

typedef void (CALLBACK* DOMVisitCallBack)(int, HANDLE);

class FBroDOMVisitor :public CefDOMVisitor, public FBroHsEventModel<FBroHsDOMVisitor>
{
public:
	FBroDOMVisitor(int flag, HANDLE callback);
	FBroDOMVisitor(CefRefPtr<FBroHsDOMVisitor> hscallback);
	FBroDOMVisitor(FBroHsDOMVisitor* hscallback);
	~FBroDOMVisitor();

	virtual void Visit(CefRefPtr<CefDOMDocument> document)override;
private:
	DOMVisitCallBack m_callback = NULL;
	int m_flag = 0;
protected:
	IMPLEMENT_REFCOUNTING(FBroDOMVisitor);
};

#ifndef _FBROELIB
DLLEXPORT BOOL TEXPORTS FBroHsBrowserFrame_IsValid(CefRefPtr<CefFrame> frame);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowserFrame_GetURL(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_Undo(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_Redo(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_Cut(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_Copy(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_Paste(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_Delete(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_SelectAll(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_ViewSource(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_LoadURL(CefRefPtr<CefFrame> frame, const CefString& url);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserFrame_IsMain(CefRefPtr<CefFrame> frame);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserFrame_IsFocused(CefRefPtr<CefFrame> frame);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowserFrame_GetName(CefRefPtr<CefFrame> frame);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowserFrame_GetIdentifier(CefRefPtr<CefFrame> frame);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_LoadRequest(CefRefPtr<CefFrame> frame, CefRefPtr<CefRequest> pObject);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_SendProcessMessage(CefRefPtr<CefFrame> frame, CefProcessId target_process, CefRefPtr<CefProcessMessage> message);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_ExecuteJavaScript(CefRefPtr<CefFrame> frame, const CefString& code, const CefString& script_url, int start_line);
DLLEXPORT CefRefPtr<CefV8Context> TEXPORTS FBroHsBrowserFrame_GetV8Context(CefRefPtr<CefFrame> frame);
DLLEXPORT CefRefPtr<CefFrame> TEXPORTS FBroHsBrowserFrame_GetParent(CefRefPtr<CefFrame> frame);
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsBrowserFrame_GetBrowser(CefRefPtr<CefFrame> frame);

//DLLEXPORT void TEXPORTS FBroHsBrowserFrame_GetSourceStatic(CefRefPtr<CefFrame> frame, FBroHsStringVisitor* hsvisitor);
//DLLEXPORT void TEXPORTS FBroHsBrowserFrame_GetTextStatic(CefRefPtr<CefFrame> frame, FBroHsStringVisitor* hsvisitor);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_GetSource(CefRefPtr<CefFrame> frame, CefRefPtr<FBroHsStringVisitor> hsvisitor);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_GetText(CefRefPtr<CefFrame> frame, CefRefPtr<FBroHsStringVisitor> hsvisitor);

//DLLEXPORT void TEXPORTS FBroHsBrowserFrame_ExecuteJavaScriptToHasReturnStatic(CefRefPtr<CefFrame> frame, const CefString& code, const CefString& script_url, int start_line, FBroHsJsCallback* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_ExecuteJavaScriptToHasReturn(CefRefPtr<CefFrame> frame, const CefString& code, const CefString& script_url, int start_line, CefRefPtr<FBroHsJsCallback> callback);

//DLLEXPORT void TEXPORTS FBroHsBrowserFrame_VisitDOMStatic(CefRefPtr<CefFrame> frame, FBroHsDOMVisitor* callback);
DLLEXPORT void TEXPORTS FBroHsBrowserFrame_VisitDOM(CefRefPtr<CefFrame> frame, CefRefPtr<FBroHsDOMVisitor> callback);

DLLEXPORT void TEXPORTS FBroHsBrowserFrame_CreateURLRequest(CefRefPtr<CefFrame> frame, CefRefPtr<CefRequest> request, CefRefPtr<FBroHsURLRequestClient> hsevent, int64_t flag);

#else

//void TEXPORTS FBroHsBrowserFrame_ExecuteJavaScriptToHasReturnStatic(CefRefPtr<CefFrame> frame, const CefString& code, const CefString& script_url, int start_line, FBroHsJsCallback* callback);
void TEXPORTS FBroHsBrowserFrame_ExecuteJavaScriptToHasReturn(CefRefPtr<CefFrame> frame, const CefString& code, const CefString& script_url, int start_line, CefRefPtr<FBroHsJsCallback> callback);

#endif // _FBROELIB




#ifdef _FBROELIB
namespace FBrowserE {
	void TEXPORTS FBroBrowserFrame_ExecuteJavaScriptToHasReturn(CefFrame* frame, const char* code, const char* script_url, int start_line, int flag, ExecuteJavaScript_callback callback);
}
#endif

#endif