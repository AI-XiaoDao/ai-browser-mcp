
#ifndef __VOL_NETWORK_H__
#define __VOL_NETWORK_H__

#define _VS_DEFAULT_PORT  19730

#define _VSM_DATA_INCOMING  WM_APP + 120
#define _VSM_ACCEPT         WM_APP + 121
#define _VSM_CLOSE          WM_APP + 122

#define _VOL_SOCKET_MSG_FIRST  _VSM_DATA_INCOMING
#define _VOL_SOCKET_MSG_LAST   _VSM_CLOSE

//----------------------------------------------------------------------------

class IVolSocketInterface
{
public:
    virtual void OnRecvUDPData (CVolMem& memData, CVolString& strFromAddr, INT nFromPort)  { }
    virtual void OnRecvPeerData (CVolMem& memData)  { }
    virtual void OnServerCloseConnect ()  { }

    virtual void OnRecvClientData (CVolMem& memData, const TCHAR* szClient)  { }
    virtual void OnClientEntry (const TCHAR* szClient)  { }
    virtual void OnClientLeave (const TCHAR* szClient)  { }

    virtual void OnRecvClientData2 (CVolMem& memData, const INT_P npSocketHandle)  { }
    virtual void OnClientEntry2 (const INT_P npSocketHandle)  { }
    virtual void OnClientLeave2 (const INT_P npSocketHandle)  { }
};

class CBaseSocketObjct : public CVolCommonBase, public IVolWndMsgFilter
{
public:
    CBaseSocketObjct ();
    ~CBaseSocketObjct ();

public:
    virtual BOOL Create (IVolSocketInterface* pSocketInterface);
    virtual BOOL CreateSocket ()  { return FALSE; }

    static BOOL_P FillAddr (SOCKADDR_IN* pdest, const TCHAR* szHostName, INT nPort);
    static BOOL_P sFillNetAddr (IN_ADDR* pInAddr, const TCHAR* szHostName, const BOOL_P blpEnableAnyAddress);
    static BOOL sSendData (SOCKET hSocket, const BYTE* pData, INT nDataSize, INT nWaitSeconds);
    BOOL SetSockOption (int level, int optname, const void* optval, int optlen);

protected:
    void MCloseSocket (SOCKET hSock);

protected:
    CVolMsgFilterWindow<_VOL_SOCKET_MSG_FIRST, _VOL_SOCKET_MSG_LAST> m_wndFilter;
    IVolSocketInterface* m_pSocketInterface;

    SOCKET m_hSock;
};

//----------------------------------------------------------------------------

class CUDPSocketObject : public CBaseSocketObjct
{
public:
    inline_ CUDPSocketObject ()
    {
        m_nPort = 0;
    }

public:
    virtual BOOL CreateSocket () override;

    void ChangePort (INT nNewPort);
    inline_ INT GetPort () const  { return m_nPort; }

    BOOL SendText (const TCHAR* szHostName, INT nPort, const TCHAR* str);
    BOOL SendData (const TCHAR* szHostName, INT nPort, const BYTE* pData, INT nDataSize);

protected:
    virtual void OnFilterMessage (UINT uMsg, WPARAM wParam, LPARAM lParam) override;

protected:
    INT m_nPort;
};

//----------------------------------------------------------------------------

class CClientSockObject : public CBaseSocketObjct
{
public:
    inline_ CClientSockObject ()
    {
        m_blConnected = FALSE;
    }

public:
    virtual BOOL Create (IVolSocketInterface* pSocketInterface) override;
    virtual BOOL CreateSocket () override;

    BOOL ConnectServer (const TCHAR* szServerHostName, INT nServerPort);
    void CloseConnection ();

    // nWaitSeconds == -1 表示无限时等待。
    BOOL SendText (const TCHAR* str, INT nWaitSeconds = -1);
    BOOL SendData (const BYTE* pData, INT nDataSize, INT nWaitSeconds = -1);

    inline_ BOOL IsConnected () const
    {
        return m_blConnected;
    }

protected:
    virtual void OnFilterMessage (UINT uMsg, WPARAM wParam, LPARAM lParam) override;

    BOOL m_blConnected;
};

//----------------------------------------------------------------------------

class CServerSockObject : public CBaseSocketObjct
{
public:
    inline_ CServerSockObject ()
    {
        m_nPort = _VS_DEFAULT_PORT;
    }

    inline_ ~CServerSockObject ()
    {
        Close ();
    }

public:
    virtual BOOL CreateSocket () override;

    void ChangePort (INT nNewPort);
    inline_ INT GetPort () const  { return m_nPort; }
    void Close ();

    // szClient为空文本表示向所有客户发送数据
    // nWaitSeconds == -1 表示无限时等待。
    BOOL SendData (const TCHAR* szClient, const BYTE* pData, INT nDataSize, INT nWaitSeconds = -1);

    void CloseSpecClientConnect (const TCHAR* szClient);
    
    inline_ const TCHAR* GetClient (const INT_P npClientIndex) const
    {
        return (m_saryClient.IsIndexValid (npClientIndex) ? m_saryClient [npClientIndex] : _T (""));
    }

    inline_ INT GetNumClients () const
    {
        return (INT)m_saryClient.GetCount ();
    }

    inline_ INT_P GetClientSocket (const INT_P npClientIndex) const
    {
        return (INT_P)(m_arySockets.IsIndexValid (npClientIndex) ? m_arySockets [npClientIndex] : INVALID_SOCKET);
    }

    inline_ INT_P FindClientSocket (const TCHAR* szClient) const
    {
        return GetClientSocket (m_saryClient.FindFirstElement (szClient));
    }

protected:
    virtual void OnFilterMessage (UINT uMsg, WPARAM wParam, LPARAM lParam) override;

    void OnAccept (WPARAM wParam, LPARAM);
    void OnDataIncoming (WPARAM wParam, LPARAM lParam);

protected:
    CMUIntPArray m_arySockets;
    CMStringArray m_saryClient;
    INT m_nPort;
};

//----------------------------------------------------------------------------

class CServerSockObject2 : public CBaseSocketObjct
{
public:
    inline_ CServerSockObject2 ()
    {
        m_nPort = _VS_DEFAULT_PORT;
    }

public:
    virtual BOOL CreateSocket () override;

    void ChangePort (INT nNewPort);
    inline_ INT GetPort () const  { return m_nPort; }
    void Close ();

    void CloseSpecClientConnect (const INT_P npSocketHandle);
    static CVolString& sGetPeerAddress (const INT_P npSocketHandle, CVolString& strAddress);
    
protected:
    virtual void OnFilterMessage (UINT uMsg, WPARAM wParam, LPARAM lParam) override;

    void OnAccept (WPARAM wParam, LPARAM);
    void OnDataIncoming (WPARAM wParam, LPARAM lParam);

protected:
    INT m_nPort;
};

//----------------------------------------------------------------------------

class CVolPinger : public CVolCommonBase
{
public:
    inline_ CVolPinger ()
    {
        m_hICMPLib = NULL;
    }

    ~CVolPinger ();

public:
    // nPingTimeout: 等待时间，单位毫秒。
    // 如果失败，返回 -1 ，否则返回被 ping 机器响应时间，单位毫秒。
    INT ping (const TCHAR* szHostName, INT nPingTimeout = 10 * 1000);

protected:
    HINSTANCE m_hICMPLib;
};

#endif
