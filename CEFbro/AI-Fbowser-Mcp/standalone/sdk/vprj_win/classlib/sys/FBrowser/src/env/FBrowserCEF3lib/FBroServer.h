#pragma once
#ifndef FBROWSER_SERVER_H_
#define FBROWSER_SERVER_H_

class FBroString;
class FBroDoubleString;
class FBroHsServerHandle;

typedef void (CALLBACK* OnServerCreatedCallBack)(HANDLE);
typedef void (CALLBACK* OnServerDestroyedCallBack)(HANDLE);
typedef void (CALLBACK* OnClientConnectedCallBack)(HANDLE, int);
typedef void (CALLBACK* OnClientDisconnectedCallBack)(HANDLE, int);
typedef void (CALLBACK* OnHttpRequestCallBack)(HANDLE, int, const char*, HANDLE);
typedef BOOL (CALLBACK* OnWebSocketRequestCallBack)(HANDLE, int, const char*, HANDLE);
typedef void (CALLBACK* OnWebSocketConnectedCallBack)(HANDLE, int);
typedef void (CALLBACK* OnWebSocketMessageCallBack)(HANDLE, int, const void*, int);


extern OnServerCreatedCallBack onservercreatcallback;
extern OnServerDestroyedCallBack onserverdestroyedcallback;
extern OnClientConnectedCallBack onclientconnectedcallback;
extern OnClientDisconnectedCallBack onclientdisconnectedcallback;
extern OnHttpRequestCallBack onhttprequestcallback;
extern OnWebSocketRequestCallBack onwebsocketrequestcallback;
extern OnWebSocketConnectedCallBack onwebsocketconnectedcallback;
extern OnWebSocketMessageCallBack onwebsocketmessagecallback;



void TEXPORTS FBroServer_HookServerEvent(HANDLE inonservercreatcallback,
    HANDLE inonserverdestroyedcallback,
    HANDLE inonclientconnectedcallback,
    HANDLE inonclientdisconnectedcallback,
    HANDLE inonhttprequestcallback,
    HANDLE inonwebsocketrequestcallback,
    HANDLE inonwebsocketconnectedcallback,
    HANDLE inonwebsocketmessagecallback);

#ifndef _FBROELIB

//DLLEXPORT void TEXPORTS FBroHsServer_CreateServerStatic(const CefString& url, int port, int maxconnections, FBroHsServerHandle* callback);
DLLEXPORT void TEXPORTS FBroHsServer_CreateServer(const CefString& url, int port, int maxconnections, CefRefPtr<FBroHsServerHandle> callback);
void TEXPORTS FBroServer_CreateServer(char* url, int port, int maxconnections);

DLLEXPORT void TEXPORTS FBroHsServer_Shutdown(CefRefPtr<CefServer> server);
DLLEXPORT BOOL TEXPORTS FBroHsServer_IsRunning(CefRefPtr<CefServer> server);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsServer_GetAddress(CefRefPtr<CefServer> server);
DLLEXPORT BOOL TEXPORTS FBroHsServer_HasConnection(CefRefPtr<CefServer> server);
DLLEXPORT BOOL TEXPORTS FBroHsServer_IsValidConnection(CefRefPtr<CefServer> server, int connectionid);
DLLEXPORT void TEXPORTS FBroHsServer_SendHttp200Response(CefRefPtr<CefServer> server, int connectionid, const CefString& contenttype, const void* data, int size);
DLLEXPORT void TEXPORTS FBroHsServer_SendHttp404Response(CefRefPtr<CefServer> server, int connectionid);
DLLEXPORT void TEXPORTS FBroHsServer_SendHttp500Response(CefRefPtr<CefServer> server, int connectionid, const CefString& errormessage);
DLLEXPORT CefRefPtr<CefTaskRunner> TEXPORTS FBroHsServer_GetTaskRunner(CefRefPtr<CefServer> server);
DLLEXPORT void TEXPORTS FBroHsServer_SendRawData(CefRefPtr<CefServer> server, int connectionid, void* data, int size);
DLLEXPORT void TEXPORTS FBroHsServer_CloseConnection(CefRefPtr<CefServer> server, int connectionid);
DLLEXPORT void TEXPORTS FBroHsServer_SendWebSocketMessage(CefRefPtr<CefServer> server, int connectionid, const void* data, int size);
DLLEXPORT void TEXPORTS FBroHsServer_SendHttpResponse(CefRefPtr<CefServer> server, int connectionid, int responsecode, const CefString& contenttype, int contentlength, CefRefPtr<FBroDoubleString> indata);

#endif // !_FBROELIB




////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#endif