#pragma once
#include "FBroBaseEvent.h"

class FBroHsDevToolsMessageObserver;
class FBroHsGeneralResultCallback;
class CefBrowser;

class FBroHsDevToolsMessageObserver :public FBroBaseEvent
{
public:
    virtual bool OnDevToolsMessage(CefRefPtr<CefBrowser> browser,
        const void* message,
        size_t message_size) {
        return false;
    };

    virtual void OnDevToolsMethodResult(CefRefPtr<CefBrowser> browser,
        int message_id,
        bool success,
        const void* result,
        size_t result_size) {};


    virtual void OnDevToolsEvent(CefRefPtr<CefBrowser> browser,
        const CefString& method,
        const void* params,
        size_t params_size) {};

    virtual void OnDevToolsAgentAttached(CefRefPtr<CefBrowser> browser) {};

    virtual void OnDevToolsAgentDetached(CefRefPtr<CefBrowser> browser) {};

protected:
    IMPLEMENT_REFCOUNTING(FBroHsDevToolsMessageObserver);
};

class FBroHsGeneralResultCallback : public FBroBaseEvent {

public:
    virtual void Callback_Data(CefRefPtr<CefBrowser> browser,
        int message_id,
        bool success,
        const void* data,
        size_t datasize) {};

    virtual void Callback_ListData(CefRefPtr<CefBrowser> browser,
        int message_id,
        bool success,
        CefRefPtr<CefListValue> listvalue) {};
protected:
    IMPLEMENT_REFCOUNTING(FBroHsGeneralResultCallback);
};