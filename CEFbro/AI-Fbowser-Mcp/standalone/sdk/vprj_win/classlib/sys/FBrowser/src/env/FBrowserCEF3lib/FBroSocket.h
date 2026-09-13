#pragma once
#ifndef FBROWSER_SOCKET_H_
#define FBROWSER_SOCKET_H_

class M_SocketClient;
class M_SocketServer;

extern std::unique_ptr<M_SocketServer> m_socketserver;

void AddSocketClientList(std::shared_ptr<M_SocketClient> client);
void SendHeartToSocketClientList();
std::shared_ptr<M_SocketClient> FindSocketClientListByBrowser(CefRefPtr<CefBrowser> browser);
void DeleteSocketClientListByBrowser(CefRefPtr<CefBrowser> browser);
void CloseSocketClientListByBrowser(CefRefPtr<CefBrowser> browser);
void CloseALLSocketClientList();


#ifndef _FBROELIB

DLLEXPORT int TEXPORTS FBroHsSocketServer_SendByBrowser(CefRefPtr<CefBrowser> browser, const char* name, const char* data, int size);
DLLEXPORT BOOL TEXPORTS FBroHsSocketServer_SendByBrowserProcessID(CefRefPtr<CefBrowser> browser, DWORD processid, const char* name, const char* data, int size);
DLLEXPORT int TEXPORTS FBroHsSocketServer_GetProcessIDCountByBrowser(CefRefPtr<CefBrowser> browser);
DLLEXPORT int TEXPORTS FBroHsSocketServer_GetProcessIDListByBrowser(CefRefPtr<CefBrowser> browser, DWORD* retdata);

DLLEXPORT BOOL TEXPORTS FBroHsSocketClient_SendByBrowser(CefRefPtr<CefBrowser> browser, const char* name, const char* data, int size);

#endif // !_FBROELIB


void TEXPORTS ReceiveRenderProcessMessage(CefRefPtr<CefBrowser> browser, DWORD processid, const CefString& name, std::unique_ptr<char[]> message, int size);

void TEXPORTS ReceiveMainProcessMessage(CefRefPtr<CefBrowser> browser, const CefString& name, std::unique_ptr<char[]> message, int size);


void ReceiveMainProcessMessageForCmd(const std::string& cmd);

#endif