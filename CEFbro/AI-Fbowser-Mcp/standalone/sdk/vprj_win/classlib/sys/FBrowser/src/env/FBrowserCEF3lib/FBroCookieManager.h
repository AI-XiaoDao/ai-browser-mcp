#pragma once
#ifndef FBROWSER_COOKIEMANAGER_H_
#define FBROWSER_COOKIEMANAGER_H_

#include "FBroHsBaseEvent.h"

class FBroHsCookieVisitor;
class FBroCefStringList;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefCookieManager> TEXPORTS FBroHsCookieManager_GetGlobalManager();

//DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_VisitAllCookiesStatic(CefRefPtr<CefCookieManager> CookieManager, FBroHsCookieVisitor* callback);
//DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_VisitUrlCookiesStatic(CefRefPtr<CefCookieManager> CookieManager, const CefString& url, BOOL includeHttpOnly, FBroHsCookieVisitor* callback);
DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_VisitAllCookies(CefRefPtr<CefCookieManager> CookieManager, CefRefPtr<FBroHsCookieVisitor> callback);
DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_VisitUrlCookies(CefRefPtr<CefCookieManager> CookieManager, const CefString& url, BOOL includeHttpOnly, CefRefPtr<FBroHsCookieVisitor> callback);

DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_SetCookie(CefRefPtr<CefCookieManager> CookieManager, const CefString& url, POINT_COOKIEDATA inCookieData);
DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_DeleteCookies(CefRefPtr<CefCookieManager> CookieManager, const CefString& url, const CefString& cookie_name);
DLLEXPORT BOOL TEXPORTS FBroHsCookieManager_FlushStore(CefRefPtr<CefCookieManager> CookieManager);
DLLEXPORT void TEXPORTS FBroHsCookieManager_SetSupportedSchemes(CefRefPtr<CefCookieManager> CookieManager, CefRefPtr<FBroCefStringList> inschemes, BOOL include_defaults);

#endif // !_FBROELIB



typedef BOOL(CALLBACK* CookieVisitor_callback)(int,HANDLE,int,int,BOOL &);

class FBroCookieVisitor :public CefCookieVisitor,public FBroHsEventModel<FBroHsCookieVisitor>
{
public:
	FBroCookieVisitor(HANDLE callback, int flag);
	FBroCookieVisitor(CefRefPtr<FBroHsCookieVisitor> hscallback);
	FBroCookieVisitor(FBroHsCookieVisitor* hscallback);
	~FBroCookieVisitor();

public:
	virtual bool Visit(const CefCookie& cookie,
		int count,
		int total,
		bool& deleteCookie)override;

private:
	CookieVisitor_callback m_callback = NULL;
	int m_total = 0;
	int m_flag = 0;

protected:
	IMPLEMENT_REFCOUNTING(FBroCookieVisitor);

};

#endif