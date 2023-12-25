import ctypes
import win32api
import win32security


def hibernate(to_hibernate=True):
    """Puts Windows to Suspend/Sleep/Standby or Hibernate.

    Parameters
    ----------
    to_hibernate: bool, default True
        If True (default), system will Hibernate, but only if Hibernate is enabled in the
        system settings. If it's not, system will Sleep.
        If False, system will enter Suspend/Sleep/Standby state.
    """
    # Enable the SeShutdown privilege (which must be present in your
    # token in the first place)
    priv_flags = (win32security.TOKEN_ADJUST_PRIVILEGES |
                  win32security.TOKEN_QUERY)
    h_token = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        priv_flags
    )
    priv_id = win32security.LookupPrivilegeValue(
        None,
        win32security.SE_SHUTDOWN_NAME
    )
    old_privs = win32security.AdjustTokenPrivileges(
        h_token,
        0,
        [(priv_id, win32security.SE_PRIVILEGE_ENABLED)]
    )

    if not win32api.GetPwrCapabilities()['HiberFilePresent'] and to_hibernate:
        import warnings
        warnings.warn("Hibernate isn't available. Suspending.")
    try:
        ctypes.windll.powrprof.SetSuspendState(not to_hibernate, True, False)
    except:
        # True=> Standby; False=> Hibernate
        # https://msdn.microsoft.com/pt-br/library/windows/desktop/aa373206(v=vs.85).aspx
        # says the second parameter has no effect.
        #        ctypes.windll.kernel32.SetSystemPowerState(not hibernate, True)
        win32api.SetSystemPowerState(not to_hibernate, True)

    # Restore previous privileges
    win32security.AdjustTokenPrivileges(
        h_token,
        0,
        old_privs
    )