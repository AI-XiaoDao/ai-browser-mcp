#pragma once

#include "FBroHsBaseEvent.h"

class CefServerHandler;
class FBroHsServerHandle;

class FBroServerHandle :public CefServerHandler,public FBroHsEventModel<FBroHsServerHandle>
{
public:
    FBroServerHandle();

    FBroServerHandle(FBroHsServerHandle* callback);

    FBroServerHandle(CefRefPtr<FBroHsServerHandle> callback);

    ~FBroServerHandle();

    virtual void OnServerCreated(CefRefPtr<CefServer> server) override;

    virtual void OnServerDestroyed(CefRefPtr<CefServer> server) override;

    virtual void OnClientConnected(CefRefPtr<CefServer> server,
        int connection_id) override;

    virtual void OnClientDisconnected(CefRefPtr<CefServer> server,
        int connection_id) override;

    virtual void OnHttpRequest(CefRefPtr<CefServer> server,
        int connection_id,
        const CefString& client_address,
        CefRefPtr<CefRequest> request)override;

    virtual void OnWebSocketRequest(CefRefPtr<CefServer> server,
        int connection_id,
        const CefString& client_address,
        CefRefPtr<CefRequest> request,
        CefRefPtr<CefCallback> callback) override;

    virtual void OnWebSocketConnected(CefRefPtr<CefServer> server,
        int connection_id) override;

    virtual void OnWebSocketMessage(CefRefPtr<CefServer> server,
        int connection_id,
        const void* data,
        size_t data_size) override;

protected:
    IMPLEMENT_REFCOUNTING(FBroServerHandle);
};