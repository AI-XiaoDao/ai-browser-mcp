#ifndef _vol_sqlite3_h
#define _vol_sqlite3_h

#include <sqlite3.h>

class CSqliteWraper
{
	private:
		sqlite3* data = NULL;
	public:
		CSqliteWraper() {}
		
		sqlite3* GetData()
		{
			return data; 
		}
		void SetData(sqlite3* ptr)
		{
			data = ptr;
		}
		INT Close()
		{
			if (data)
			{
				INT result = sqlite3_close_v2(data);
				data = NULL;
				return result;
			}
			return 0;
		}
		~CSqliteWraper() 
		{ 
			Close();
		}
};

class CSqliteStmtWraper : public CVolCommonBase
{
	private:
		sqlite3_stmt* data = NULL;
	public:
		CSqliteStmtWraper() {}
		
		sqlite3_stmt* GetData()
		{
			return data; 
		}
		void SetData(INT_P ptr)
		{
			data = (sqlite3_stmt*)ptr;
		}
		void Close()
		{
			if (data)
			{
				sqlite3_finalize(data);
				data = NULL;
			}
		}
		~CSqliteStmtWraper() 
		{ 
			Close();
		}
};
#endif /* _vol_sqlite3_h */