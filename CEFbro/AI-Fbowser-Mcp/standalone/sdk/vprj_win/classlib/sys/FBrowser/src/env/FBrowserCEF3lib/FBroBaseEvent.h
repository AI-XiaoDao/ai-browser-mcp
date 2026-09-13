#pragma once

typedef enum {
	BEGIN = 1000,
	ResourceHandlerType,
	ResponseFilterType,
	InitEventType,
	BroEventType,
	DownloadImageCallbackType,
	FileDialogCallbackType,
	PdfPrintCallbackType,
	StringVisitorType,
	JsCallbackType,
	DOMVisitorType,
	TaskType,
	CookieVisitorType,
	QueryHandlerType,
	V8HandlerType,
	V8AccessorType,
	V8InterceptorType,
	ServerHandleType,
	ExtensionHandlerType,
	ClearCacheCallbackType,
	DevToolsMessageObserverType,
	GeneralResultCallbackType,
	URLRequestClientType,
	END = URLRequestClientType
} FBroBaseEventType;


class FBroBaseEvent :virtual public CefBaseRefCounted {
public:
	FBroBaseEventType type_ = BEGIN;

protected:
	IMPLEMENT_REFCOUNTING(FBroBaseEvent);
};