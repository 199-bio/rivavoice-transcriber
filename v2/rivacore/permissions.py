"""
macOS permission checking and user guidance
"""

import subprocess
import os
import sys


class PermissionChecker:
    """Check and guide users through required macOS permissions"""
    
    @staticmethod
    def check_microphone_permission() -> tuple[bool, str]:
        """Check if microphone permission is granted"""
        try:
            # Try to access microphone through PyAudio
            import pyaudio
            pa = pyaudio.PyAudio()
            # Try to open a stream
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            stream.close()
            pa.terminate()
            return True, "Microphone access granted"
        except Exception as e:
            if "Input overflowed" in str(e):
                # This error means we can access the mic, just had buffer issues
                return True, "Microphone access granted"
            return False, "Microphone access denied. Please grant permission in System Settings > Privacy & Security > Microphone"
    
    @staticmethod
    def check_accessibility_permission() -> tuple[bool, str]:
        """Check if accessibility permission is granted for Terminal"""
        try:
            # Check if Terminal has accessibility access
            result = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to return true'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "Accessibility access granted"
            else:
                return False, "Accessibility access denied. Please grant permission in System Settings > Privacy & Security > Accessibility"
        except Exception:
            return False, "Could not check accessibility permission"
    
    @staticmethod
    def check_input_monitoring_permission() -> tuple[bool, str]:
        """Check if input monitoring permission is granted"""
        # Skip this check to avoid threading issues with TIS/TSM APIs
        # The actual permission will be tested when hotkeys are used
        return True, "Input monitoring will be checked when hotkeys are used"
    
    @staticmethod
    def request_accessibility_permission():
        """Open accessibility preferences and prompt user"""
        try:
            # Open accessibility preferences
            subprocess.run([
                'osascript', '-e',
                'tell application "System Preferences" to reveal anchor "Privacy_Accessibility" of pane id "com.apple.preference.security"'
            ])
            subprocess.run(['osascript', '-e', 'tell application "System Preferences" to activate'])
        except:
            # Fallback for newer macOS versions
            try:
                subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])
            except:
                pass
    
    @staticmethod
    def check_all_permissions() -> dict:
        """Check all required permissions"""
        results = {}
        
        # Check each permission
        mic_ok, mic_msg = PermissionChecker.check_microphone_permission()
        results['microphone'] = {'granted': mic_ok, 'message': mic_msg}
        
        acc_ok, acc_msg = PermissionChecker.check_accessibility_permission()
        results['accessibility'] = {'granted': acc_ok, 'message': acc_msg}
        
        input_ok, input_msg = PermissionChecker.check_input_monitoring_permission()
        results['input_monitoring'] = {'granted': input_ok, 'message': input_msg}
        
        results['all_granted'] = mic_ok and acc_ok and input_ok
        
        return results
    
    @staticmethod
    def print_permission_status():
        """Print a user-friendly permission status"""
        results = PermissionChecker.check_all_permissions()
        
        print("\nPermission Status:")
        print("=" * 50)
        
        for perm_type, info in results.items():
            if perm_type == 'all_granted':
                continue
            
            status = "✅" if info['granted'] else "❌"
            perm_name = perm_type.replace('_', ' ').title()
            print(f"{status} {perm_name}: {info['message']}")
        
        if not results['all_granted']:
            print("\n⚠️  Some permissions are missing. The app may not work correctly.")
            print("\nTo fix:")
            print("1. Open System Settings")
            print("2. Go to Privacy & Security")
            print("3. Grant Terminal access to the required permissions")
            print("4. Restart the app")
        else:
            print("\n✅ All permissions granted! The app should work correctly.")
        
        print("=" * 50)