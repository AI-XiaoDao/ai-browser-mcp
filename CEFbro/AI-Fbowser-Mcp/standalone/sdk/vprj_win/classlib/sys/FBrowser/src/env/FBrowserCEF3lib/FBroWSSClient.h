#pragma once
#ifndef FBROWSER_WSSCLIENT_H_
#define FBROWSER_WSSCLIENT_H_

#include "include\fbrowser\fbro_wssclient.h"

class FBroString;


#ifndef _FBROELIB

//DLLEXPORT void FBroHsWSSClient_SetWssPtr(CefRefPtr<FBroDOMWssClient> wssclient, HANDLE wssPtr);

//DLLEXPORT void FBroHsWSSClient_SetIsClose(CefRefPtr<FBroDOMWssClient> wssclient);

DLLEXPORT BOOL TEXPORTS FBroHsWSSClient_IsNull(CefRefPtr<FBroDOMWssClient> wssclient);

DLLEXPORT BOOL TEXPORTS FBroHsWSSClient_IsSame(CefRefPtr<FBroDOMWssClient> wssclient, CefRefPtr<FBroDOMWssClient> that);

//连接wss服务器
DLLEXPORT void TEXPORTS FBroHsWSSClient_Connect(CefRefPtr<FBroDOMWssClient> wssclient, const CefString& url, const CefString& protocol);
//关闭连接
DLLEXPORT void TEXPORTS FBroHsWSSClient_Close(CefRefPtr<FBroDOMWssClient> wssclient);
//销毁连接
DLLEXPORT void TEXPORTS FBroHsWSSClient_Destroy(CefRefPtr<FBroDOMWssClient> wssclient);
//发送文本
DLLEXPORT void TEXPORTS FBroHsWSSClient_Send(CefRefPtr<FBroDOMWssClient> wssclient, const CefString&);
//发送数据
DLLEXPORT void TEXPORTS FBroHsWSSClient_SendData(CefRefPtr<FBroDOMWssClient> wssclient, void*, size_t);
////取连接地址
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsWSSClient_GetAddress(CefRefPtr<FBroDOMWssClient> wssclient);
////取连接端口
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsWSSClient_GetProtocol(CefRefPtr<FBroDOMWssClient> wssclient);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsWSSClient_GetExtensions(CefRefPtr<FBroDOMWssClient> wssclient);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsWSSClient_GetBinaryType(CefRefPtr<FBroDOMWssClient> wssclient);

#endif // !_FBROELIB





#endif