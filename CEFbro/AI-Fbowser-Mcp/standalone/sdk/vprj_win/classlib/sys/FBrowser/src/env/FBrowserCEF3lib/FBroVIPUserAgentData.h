#pragma once

class FBroDoubleString;

class FBroVIPUserAgentData : public virtual CefBaseRefCounted {
public:
	virtual void SetMainUserAgent(const CefString& indata) = 0;
	virtual void SetMainAcceptLanguage(const CefString& indata) = 0;
	virtual void SetMainPlatform(const CefString& indata) = 0;

	virtual const CefString& GetMainUserAgent() = 0;
	virtual const CefString& GetMainAcceptLanguage() = 0;
	virtual const CefString& GetMainPlatform() = 0;

	virtual void SetBrands(CefRefPtr<FBroDoubleString> indata) = 0;
	virtual void SetFullVersionList(CefRefPtr<FBroDoubleString> indata) = 0;
	virtual void SetFullVersion(const CefString& indata) = 0;
	virtual void SetPlatform(const CefString& indata) = 0;
	virtual void SetPlatformVersion(const CefString& indata) = 0;
	virtual void SetArchitecture(const CefString& indata) = 0;
	virtual void SetModel(const CefString& indata) = 0;
	virtual void SetMobile(BOOL indata) = 0;
	virtual void SetBitness(const CefString& indata) = 0;
	virtual void SetWow64(BOOL indata) = 0;
	virtual void SetFormFactors(CefRefPtr<FBroCefStringList> indata) = 0;

	virtual CefRefPtr<FBroDoubleString> GetBrands() = 0;
	virtual CefRefPtr<FBroDoubleString> GetFullVersionList() = 0;
	virtual const CefString& GetFullVersion() = 0;
	virtual const CefString& GetPlatform() = 0;
	virtual const CefString& GetPlatformVersion() = 0;
	virtual const CefString& GetArchitecture() = 0;
	virtual const CefString& GetModel() = 0;
	virtual BOOL GetMobile() = 0;
	virtual const CefString& GetBitness() = 0;
	virtual BOOL GetWow64() = 0;
	virtual CefRefPtr<FBroCefStringList> GetFormFactors() = 0;
};