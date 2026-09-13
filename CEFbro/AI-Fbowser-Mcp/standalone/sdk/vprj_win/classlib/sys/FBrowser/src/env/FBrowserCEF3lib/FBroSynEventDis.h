#pragma once

#include "FBroMiddleData.h"

class SynEventDis {

	struct BITDATA
	{
		void* data = NULL;
		int size = 0;
	};

	template <typename T>
	class TypeDataHasSet
	{
	public:
		TypeDataHasSet() {
			ClearData();
		}
		TypeDataHasSet(T data) {
			_data = data;
			_havData = true;
		}
		void ClearData() {
			_data = T();
			_havData = false;
		}
		bool HavData()
		{
			return _havData;
		}
		T GetData() {
			return _data;
		}
	private:
		bool _havData = false;
		T _data = T();

	};

public:
	SynEventDis();
	~SynEventDis();

	BOOL ResetEvent();

	BOOL SetEvent();

	int WaitEvent(int);

	void ClearData();

	void SetIntData(int);
	void SetDoubleData(double);
	void SetBoolData(BOOL);
	void SetStringData(const char*);
	void SetWStringData(const CefString&);
	void SetBitData(const void*, int);
	void AddBitData(const void*, int);
	void SetCefBrowser(CefRefPtr<CefBrowser>);
	void SetCefFrame(CefRefPtr<CefFrame>);
	void SetCefDictionaryValue(CefRefPtr<CefDictionaryValue>);


	BOOL HavIntData();
	BOOL HavDoubleData();
	BOOL HavBoolData();
	BOOL HavStringData();
	BOOL HavWStringData();
	BOOL HavBitData();
	BOOL HavCefBrowser();
	BOOL HavCefFrame();
	BOOL HavCefDictionaryValue();

	int GetIntData();
	double GetDoubleData();
	BOOL GetBoolData();
	std::string GetStringData();
	std::wstring GetWStringData();
	int GetBitDataSize();
	void GetBitData(void*, int, int offsize = 0);
	CefRefPtr<CefBrowser> GetCefBrowser();
	CefRefPtr<CefFrame> GetCefFrame();
	CefRefPtr<CefDictionaryValue> GetCefDictionaryValue();

private:
	HANDLE _eventHandle = NULL;

	TypeDataHasSet<int> _intData;
	TypeDataHasSet<double> _doubleData;
	TypeDataHasSet<BOOL> _boolData;

	TypeDataHasSet<std::string> _stringdata;
	TypeDataHasSet<std::wstring> _wStringData;

	BITDATA _bitData;


	CefRefPtr<CefBrowser> _browser = nullptr;
	CefRefPtr<CefFrame> _frame = nullptr;
	CefRefPtr<CefDictionaryValue> _dictionaryValue = nullptr;
	std::atomic<bool> waiting_ = false;
};


DLLEXPORT HANDLE TEXPORTS FBroSynEventDis_CreatEvent();
DLLEXPORT void TEXPORTS FBroSynEventDis_CloseEvent(SynEventDis* synEvent);

DLLEXPORT BOOL TEXPORTS FBroSynEventDis_IsValid(SynEventDis* synEvent);

DLLEXPORT BOOL TEXPORTS FBroSynEventDis_ResetEvent(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_SetEvent(SynEventDis* synEvent);
DLLEXPORT int TEXPORTS FBroSynEventDis_WaitEvent(SynEventDis* synEvent, int overTime);


DLLEXPORT void TEXPORTS FBroSynEventDis_ClearData(SynEventDis* synEvent);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetIntData(SynEventDis* synEvent, int data);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetDoubleData(SynEventDis* synEvent, double data);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetBoolData(SynEventDis* synEvent, BOOL data);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetStringData(SynEventDis* synEvent, const char* data);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetWStringData(SynEventDis* synEvent, const CefString& data);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetBitData(SynEventDis* synEvent, const void* data, int size);
DLLEXPORT void TEXPORTS FBroSynEventDis_AddBitData(SynEventDis* synEvent, const void* data, int size);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetCefBrowser(SynEventDis* synEvent, CefBrowser* browser);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetCefFrame(SynEventDis* synEvent, CefFrame* frame);
DLLEXPORT void TEXPORTS FBroSynEventDis_SetCefDictionaryValue(SynEventDis* synEvent, CefDictionaryValue* dictionaryValue);

DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavIntData(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavDoubleData(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavBoolData(SynEventDis* synEvent);

DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavWStringData(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavBitData(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavCefBrowser(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavCefFrame(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavCefDictionaryValue(SynEventDis* synEvent);

DLLEXPORT int TEXPORTS FBroSynEventDis_GetIntData(SynEventDis* synEvent);
DLLEXPORT double TEXPORTS FBroSynEventDis_GetDoubleData(SynEventDis* synEvent);
DLLEXPORT BOOL TEXPORTS FBroSynEventDis_GetBoolData(SynEventDis* synEvent);

//DLLEXPORT BOOL TEXPORTS FBroSynEventDis_HavStringData(SynEventDis* synEvent);
//DLLEXPORT HANDLE TEXPORTS FBroSynEventDis_GetStringData(SynEventDis* synEvent);

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroSynEventDis_GetWStringData(SynEventDis* synEvent);
DLLEXPORT int TEXPORTS FBroSynEventDis_GetBitDataSize(SynEventDis* synEvent);
DLLEXPORT void TEXPORTS FBroSynEventDis_GetBitData(SynEventDis* synEvent, void* retdata, int size, int offsize);
DLLEXPORT CefBrowser* TEXPORTS FBroSynEventDis_GetCefBrowser(SynEventDis* synEvent);
DLLEXPORT CefFrame* TEXPORTS FBroSynEventDis_GetCefFrame(SynEventDis* synEvent);
DLLEXPORT CefDictionaryValue* TEXPORTS FBroSynEventDis_GetCefDictionaryValue(SynEventDis* synEvent);