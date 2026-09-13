#pragma once
#ifndef FBROWSER_WEBSOCKETCLIENT_H_
#define FBROWSER_WEBSOCKETCLIENT_H_

class FBroString;

class FBroWebsocket : public virtual CefBaseRefCounted
{
public:
	FBroWebsocket(CefRefPtr<CefFrame> frame, HANDLE socket);
	~FBroWebsocket();

	BOOL IsValid();
	CefString GetAddress();
	CefString GetProtocol();
	CefString GetExtensions();
	CefString GetBinaryType();
	BOOL SendText(const CefString& indata);
	BOOL SendData(void* indata, int size);

private:
	CefRefPtr<CefFrame> m_frame = nullptr;
	CefRefPtr<CefV8Context> m_v8 = nullptr;
	HANDLE m_socket = NULL;
protected:
	IMPLEMENT_REFCOUNTING(FBroWebsocket);
};


#ifndef _FBROELIB

DLLEXPORT BOOL FBroWebsocket_IsValid(CefRefPtr<FBroWebsocket> fbrowebsocket);
DLLEXPORT CefRefPtr<FBroString> FBroWebsocket_GetAddress(CefRefPtr<FBroWebsocket> fbrowebsocket);
DLLEXPORT CefRefPtr<FBroString> FBroWebsocket_GetProtocol(CefRefPtr<FBroWebsocket> fbrowebsocket);
DLLEXPORT CefRefPtr<FBroString> FBroWebsocket_GetExtensions(CefRefPtr<FBroWebsocket> fbrowebsocket);
DLLEXPORT CefRefPtr<FBroString> FBroWebsocket_GetBinaryType(CefRefPtr<FBroWebsocket> fbrowebsocket);
DLLEXPORT BOOL FBroWebsocket_SendText(CefRefPtr<FBroWebsocket> fbrowebsocket, const CefString& indata);
DLLEXPORT BOOL FBroWebsocket_SendData(CefRefPtr<FBroWebsocket> fbrowebsocket, void* indata, int size);

#endif // !_FBROELIB



#endif

