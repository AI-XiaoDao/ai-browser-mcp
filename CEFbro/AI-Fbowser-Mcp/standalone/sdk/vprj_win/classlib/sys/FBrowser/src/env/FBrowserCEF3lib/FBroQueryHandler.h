#pragma once
#ifndef FBROWSER_QUERYHANDLER_H_
#define FBROWSER_QUERYHANDLER_H_

#include "FBroHsBaseEvent.h"

class FBroHsQueryHandler;

class FBroQueryHandler :public CefMessageRouterBrowserSide::Handler, public virtual CefBaseRefCounted,public FBroHsEventModel<FBroHsQueryHandler>
{

public:
    FBroQueryHandler() {};
    ~FBroQueryHandler() {};
    void SetCallback(QUERY_FUNCTION callbackbuf);
    void SetHsCallbackStatic(FBroHsQueryHandler* hscallback);
    void SetHsCallback(CefRefPtr<FBroHsQueryHandler> hscallback);
public:
    virtual bool OnQuery(CefRefPtr<CefBrowser> browser,
        CefRefPtr<CefFrame> frame,
        int64_t query_id,
        const CefString& request,
        bool persistent,
        CefRefPtr<Callback> callback) override;

    virtual void OnQueryCanceled(CefRefPtr<CefBrowser> browser,
        CefRefPtr<CefFrame> frame,
        int64_t query_id)  override;

private:

    CefString js_query_function;
    CefString js_cancel_function;

    QUERY_FUNCTION m_callback = NULL;

protected:
    IMPLEMENT_REFCOUNTING(FBroQueryHandler);

};

#endif




