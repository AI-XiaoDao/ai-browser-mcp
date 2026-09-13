#pragma once
#ifndef FBROWSER_BROWSERLIST_CONTROL_H_
#define FBROWSER_BROWSERLIST_CONTROL_H_

#include "FBroHsEvent.h"
#include "FBroHsBaseEvent.h"

#include "FBroClient.h"
#include "FBroApp.h"


namespace HostBrowserControl {
	void AddListData(CefRefPtr<CefBrowser> browser);

	void DelListData(int browserid);
	void DelListData(CefRefPtr<CefBrowser> indata);
	void DelAllBrowserList();
	void DelAllBrowserAndClose();
	int GetBrowsercCount();

    //通过浏览器ID查找浏览器
	CefRefPtr<CefBrowser> FindBrowser(int browserid);
	//通过浏览器下标查找浏览器
	CefRefPtr<CefBrowser> FindBrowserFromIndex(int index);
	//通过浏览器窗口句柄查找浏览器
	CefRefPtr<CefBrowser> FindBrowserFromWindowHandle(HWND windowHandle);
	//通过浏览器标识查找浏览器
	CefRefPtr<CefBrowser> FindBrowser(const CefString& flag);

	CefRefPtr<CefListValue> GetBrowserIDList();

	CefRefPtr<CefListValue> GetBrowserFlagList();

}


namespace JSFunListControl {
	bool IsJSFunListMsg(const CefString& indata);

	void AddListData(CefMessageRouterConfig * config,
		QUERY_FUNCTION lpfnCallback,
		CefRefPtr<FBroHsQueryHandler> hscallback);
	void AddListData(Query_FUNCTION data);
	void DelListData(const CefString& funName);
	void DelALLData();
	std::string GetFormatString();
	void DisRenderSideRouter(CefMessageRouterRendererSidelist& renderer_side_router);
	void DisBrowserSideRouter(MessageRouterBrowserSidelist& browser_side_router_list);
}

namespace JSCallbackListControl {
	class FBroJsCallback :public CefBaseRefCounted, public FBroHsEventModel<FBroHsJsCallback> {

	public:
		FBroJsCallback(CefRefPtr<FBroHsJsCallback> callback) :FBroHsEventModel(callback) {}
		FBroJsCallback(FBroHsJsCallback* callback) :FBroHsEventModel(callback) {}
		~FBroJsCallback() {}
#ifdef _FBROELIB
		ExecuteJavaScript_callback evalFunction = NULL;
#endif
		int flag = 0;
		//int id = 0;
	private:
		IMPLEMENT_REFCOUNTING(FBroJsCallback);

	};

	void AddListData(int id, CefRefPtr<FBroJsCallback> data);
	CefRefPtr<FBroJsCallback> FindJsCallback(int id);
	void DeleteJsCallback(int id);
	void DeleteAllJsCallback();
}

//判断浏览器是否还存在
DLLEXPORT BOOL TEXPORTS FBroHsBrowserListControl_IsLife(CefRefPtr<CefBrowser> browser);

//通过ID取浏览器
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsBrowserListControl_GetBrowserFromID(int browserid);

//通过序号取浏览器
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsBrowserListControl_GetBrowserFromIndex(int index);

//通过浏览器句柄获取浏览器
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsBrowserListControl_GetBrowserFromWindowHandle(HWND windowHandle);

//通过用户标识取浏览器
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsBrowserListControl_GetBrowserFromFlag(const CefString& flag);

//取浏览器数量
DLLEXPORT int TEXPORTS FBroHsBrowserListControl_GetBrowserCount();

//取浏览器ID清单
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsBrowserListControl_GetBrowserIDList();

//取浏览器用户标识清单
DLLEXPORT CefRefPtr<CefListValue> TEXPORTS FBroHsBrowserListControl_GetBrowserFlagList();


#endif