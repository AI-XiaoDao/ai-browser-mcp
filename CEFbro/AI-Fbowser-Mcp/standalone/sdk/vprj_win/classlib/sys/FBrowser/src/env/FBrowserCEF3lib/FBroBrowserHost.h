#pragma once
#ifndef FBROWSER_BROWSERHOST_H_
#define FBROWSER_BROWSERHOST_H_

#include "FBroHsBaseEvent.h"

class FBroHsDownloadImageCallback;
class FBroCefStringList;
class FBroHsFileDialogCallback;
class FBroHsPdfPrintCallback;
class FBroHsBroEvent;
class FBroCompositionUnderlineList;
class FBroString;

class FBroPdfPrintCallback :public CefPdfPrintCallback, public FBroHsEventModel<FBroHsPdfPrintCallback>
{
public:
	FBroPdfPrintCallback(int flag, HANDLE m_callback);

	FBroPdfPrintCallback(CefRefPtr<FBroHsPdfPrintCallback> hscallback) :FBroHsEventModel(hscallback) {
	}
	FBroPdfPrintCallback(FBroHsPdfPrintCallback* hscallback) :FBroHsEventModel(hscallback) {
	}

	~FBroPdfPrintCallback() {};

private:
#ifdef _FBROELIB
	OnPdfPrintFinished_callback pfnOnPdfPrintFinished_callback = NULL;
#endif
	int m_flag = 0;
public:
	virtual void OnPdfPrintFinished(const CefString& path, bool ok)override;
protected:
	IMPLEMENT_REFCOUNTING(FBroPdfPrintCallback);
};


class FBroDownloadImageCallback :public CefDownloadImageCallback, public FBroHsEventModel<FBroHsDownloadImageCallback>
{
public:
	FBroDownloadImageCallback(CefRefPtr<FBroHsDownloadImageCallback> hscallback) :FBroHsEventModel(hscallback) {};
	FBroDownloadImageCallback(FBroHsDownloadImageCallback* hscallback) :FBroHsEventModel(hscallback) {};

	FBroDownloadImageCallback(HANDLE callback, int flag);
	~FBroDownloadImageCallback() {};

private:
#ifdef _FBROELIB
	OnDownloadImageFinished_callback pfnOnDownloadImageFinished = NULL;
#endif
public:
	virtual void OnDownloadImageFinished(const CefString& image_url,
		int http_status_code,
		CefRefPtr<CefImage> image) override;

protected:
	int _flag = 0;
	IMPLEMENT_REFCOUNTING(FBroDownloadImageCallback);

};


class FBroFileDialogCallback :public CefRunFileDialogCallback, public FBroHsEventModel<FBroHsFileDialogCallback>
{
public:
	FBroFileDialogCallback(CefRefPtr<FBroHsFileDialogCallback> hscallback, HANDLE callback, int selectfilter);
	FBroFileDialogCallback(FBroHsFileDialogCallback* hscallback, HANDLE callback, int selectfilter);
	~FBroFileDialogCallback() {};

private:
#ifdef _FBROELIB
	OnFileDialogDismissed_callback pfnOnFileDialogDismissed = NULL;
#endif
	int m_selectfilter = 0;

public:
	virtual void OnFileDialogDismissed(
		/*int selected_accept_filter,????????*/
		const std::vector<CefString>& file_paths) /*override*/;


protected:
	IMPLEMENT_REFCOUNTING(FBroFileDialogCallback);
};



//class DevToolClient:public CefClient
//	,public CefLifeSpanHandler, public FBroHsEventModel<FBroHsBroEvent>
//{
//public:
//	DevToolClient() {};
//	~DevToolClient() {};
//
//	virtual CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
//
//	virtual bool DoClose(CefRefPtr<CefBrowser> browser)  override;
//
//
//protected:
//	IMPLEMENT_REFCOUNTING(DevToolClient);
//};

#ifndef _FBROELIB
DLLEXPORT void TEXPORTS FBroHsBrowserHost_CloseBrowser(CefRefPtr<CefBrowser> browser, bool force_close);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserHost_TryCloseBrowser(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetFocus(CefRefPtr<CefBrowser> browser, bool focus);
DLLEXPORT HWND TEXPORTS FBroHsBrowserHost_GetWindowHandle(CefRefPtr<CefBrowser> browser);
DLLEXPORT HWND TEXPORTS FBroHsBrowserHost_GetOpenerWindowHandle(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserHost_HasView(CefRefPtr<CefBrowser> browser);
DLLEXPORT double TEXPORTS FBroHsBrowserHost_GetZoomLevel(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetZoomLevel(CefRefPtr<CefBrowser> browser, double zoomLevel);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_StartDownload(CefRefPtr<CefBrowser> browser, const CefString& url);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DownloadImage(CefRefPtr<CefBrowser> browser, const CefString& url, bool is_favicon, uint32_t max_image_size, bool bypass_cache, CefRefPtr<FBroHsDownloadImageCallback> hscallback);

DLLEXPORT void TEXPORTS FBroHsBrowserHost_RunFileDialog(CefRefPtr<CefBrowser> browser, int mode, const CefString& title, const CefString& defaultfliepath, CefRefPtr<FBroCefStringList> acceptfilters, CefRefPtr<FBroHsFileDialogCallback> hscallback);

DLLEXPORT void TEXPORTS FBroHsBrowserHost_Print(CefRefPtr<CefBrowser> browser);


DLLEXPORT void TEXPORTS FBroHsBrowserHost_PrintToPDF(CefRefPtr<CefBrowser> browser, const CefString& path, FBroPdfPrintSettings*, CefRefPtr<FBroHsPdfPrintCallback> hscallback);

DLLEXPORT void TEXPORTS FBroHsBrowserHost_Find(CefRefPtr<CefBrowser> browser, const CefString& searchText, bool forward, bool matchCase, bool findNext);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_StopFinding(CefRefPtr<CefBrowser> browser, bool clearSelection);
//DLLEXPORT void TEXPORTS FBroHsBrowserHost_ShowDevToolsStatic(CefRefPtr<CefBrowser> browser, const CefString& title, HWND parent, int x, int y, int nWidth, int nHeight, FBroBrowserSetting* browsersetinfo, PTELIB_ELEMENT_AT element_at, FBroHsBroEvent* hsbroevent, Pointer_Event_Disable_Control);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_ShowDevTools(CefRefPtr<CefBrowser> browser, const CefString& title, HWND parent, int x, int y, int nWidth, int nHeight, FBroBrowserSetting* browsersetinfo, PTELIB_ELEMENT_AT element_at, CefRefPtr<FBroHsBroEvent> hsbroevent, Pointer_Event_Disable_Control);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_CloseDevTools(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserHost_HasDevTools(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SendKeyEvent(CefRefPtr<CefBrowser> browser, PTELIB_KEYEVENT keyevent);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserHost_IsAudioMuted(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetAutoResizeEnabled(CefRefPtr<CefBrowser> browser, bool enabled, int min_height, int min_width, int max_height, int max_width);
DLLEXPORT CefRefPtr<CefRequestContext> TEXPORTS FBroHsBrowserHost_GetRequestContext(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetAudioMuted(CefRefPtr<CefBrowser> browser, bool mute);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SendFocusEvent(CefRefPtr<CefBrowser> browser, bool setFocus);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SendTouchEvent(CefRefPtr<CefBrowser> browser, PTELIB_TOUCH_EVENT eTouchEvent);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SendMouseWheelEvent(CefRefPtr<CefBrowser> browser, POINT_MOUSEEVENT E_MouserEvent, int deltaX, int deltaY);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SendMouseMoveEvent(CefRefPtr<CefBrowser> browser, POINT_MOUSEEVENT E_MouserEvent, bool mouseLeave);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SendMouseClickEvent(CefRefPtr<CefBrowser> browser, CefBrowserHost::MouseButtonType ButtonType, POINT_MOUSEEVENT E_MouserEvent, bool mouseUp, int clickCount);
DLLEXPORT BOOL TEXPORTS FBroHsBrowserHost_IsWindowRenderingDisabled(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_WasResized(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_WasHidden(CefRefPtr<CefBrowser> browser, BOOL hidden);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_NotifyScreenInfoChanged(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_Invalidate(CefRefPtr<CefBrowser> browser, CefBrowserHost::PaintElementType type);
DLLEXPORT int TEXPORTS FBroHsBrowserHost_GetWindowlessFrameRate(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetWindowlessFrameRate(CefRefPtr<CefBrowser> browser, int frame_rate);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_ImeSetComposition(CefRefPtr<CefBrowser> browser, const CefString& intext, CefRefPtr<FBroCompositionUnderlineList> inunderlines, POINT_RANGE inreplacement_range, POINT_RANGE inselection_range);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_ImeCommitText(CefRefPtr<CefBrowser> browser, const CefString& intext, POINT_RANGE inreplacement_range, int relative_cursor_pos);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_ImeFinishComposingText(CefRefPtr<CefBrowser> browser, BOOL keep_selection);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_ImeCancelComposition(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DragTargetDragEnter(CefRefPtr<CefBrowser> browser, CefRefPtr<CefDragData> indrag_data, POINT_MOUSEEVENT inevent, int inallowed_ops);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DragTargetDragOver(CefRefPtr<CefBrowser> browser, POINT_MOUSEEVENT inevent, int inallowed_ops);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DragTargetDragLeave(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DragTargetDrop(CefRefPtr<CefBrowser> browser, POINT_MOUSEEVENT inevent);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DragSourceEndedAt(CefRefPtr<CefBrowser> browser, int x, int y, CefBrowserHost::DragOperationsMask op);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_DragSourceSystemDragEnded(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_ShowWindows(CefRefPtr<CefBrowser> browser, BOOL show);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_MoveWindow(CefRefPtr<CefBrowser> browser, int x, int y, int nWidth, int nHeight, BOOL bRepaint);
DLLEXPORT HWND TEXPORTS FBroHsBrowserHost_GetParent(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetParent(CefRefPtr<CefBrowser> browser, HWND newparent);
DLLEXPORT void TEXPORTS FBroHsBrowserHost_SetWindowLong(CefRefPtr<CefBrowser> browser, int gwl, long newws);
DLLEXPORT long TEXPORTS FBroHsBrowserHost_GetWindowLong(CefRefPtr<CefBrowser> browser, int gwl);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowserHost_GetWindowsTitle(CefRefPtr<CefBrowser> browser);

DLLEXPORT BOOL TEXPORTS FBroHsBrowserHost_IsDevTools(CefRefPtr<CefBrowser> browser);

DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsBrowserHost_GetMainBrowser(CefRefPtr<CefBrowser> browser);
DLLEXPORT int TEXPORTS FBroHsBrowserHost_GetRuntimeStyle(CefRefPtr<CefBrowser> browser);
#endif // !_FBROELIB


#endif