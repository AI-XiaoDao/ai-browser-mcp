#pragma once
#ifndef FBROWSER_CONTEXTIDDATA_H_
#define FBROWSER_CONTEXTIDDATA_H_


struct contextdata
{
	int contextid = 0;
	int64_t renderframeid = 0;
	CefString url;
};

class FBroContextIdData :public CefBaseRefCounted
{
public:

	FBroContextIdData();
	~FBroContextIdData();

	void Clear();
	size_t GetSize();
	void AddData(int64_t inrenderframeid, CefString inurl);
	void DeleteData(int64_t inrenderframeid);

	void ToBegin() {
		m_currentiter = m_contectlist.begin();
	}
	void ToEnd() {
		m_currentiter = m_contectlist.end();
	}
	bool ToNext() {
		return (++m_currentiter) == m_contectlist.end() ? false : true;
	}
	int GetCurrentContextID() {
		if (m_currentiter == m_contectlist.end())
			return 0;
		return (*m_currentiter).contextid;
	}

public:
	//int m_browserid = 0;//当前类对应浏览器ID
	int m_maxcontextid = 0;//当前已经存储的最大ID，为了让id自己增加
	std::list<contextdata> m_contectlist;//存储当前contextid清单，一个为contextid,第二个为渲染进程传递过来的frameid，和当前浏览器的frame不一定一样，第三个是当前id的url
	std::list<contextdata>::iterator m_currentiter;

protected:

	IMPLEMENT_REFCOUNTING(FBroContextIdData);
};

namespace FBroBrowserContextData {

	typedef std::map<int, CefRefPtr<FBroContextIdData>> BrowserContextIdData;

	extern BrowserContextIdData browser_contextIdData;


	void AddMapListData(int browserid, CefRefPtr<FBroContextIdData> contextiddata);

	BrowserContextIdData::iterator FindMapListData(int browserid);
	void DeleteMapListData(int browserid);
	void AddMapListChildData(int browserid, int64_t inrenderframeid, CefString inurl);
	void DeleteMapListChildData(int browserid, int64_t inrenderframeid);
	void CLearMapListChileData(int browserid);
}

#endif