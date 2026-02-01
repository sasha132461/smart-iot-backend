import urequests
import uhashlib
import os
import machine
import time


class OTA:
    def __init__(self, url, version="1.0.0"):
        self.url = url.rstrip('/')
        self.version = version
    
    def _sha256(self, data):
        h = uhashlib.sha256(data)
        return ''.join('{:02x}'.format(b) for b in h.digest())
    
    def _compare_ver(self, v1, v2):
        p1 = [int(x) for x in v1.split('.')]
        p2 = [int(x) for x in v2.split('.')]
        for i in range(max(len(p1), len(p2))):
            a = p1[i] if i < len(p1) else 0
            b = p2[i] if i < len(p2) else 0
            if a != b:
                return a - b
        return 0
    
    def check(self):
        try:
            r = urequests.get(f"{self.url}/manifest.json")
            if r.status_code != 200:
                r.close()
                return None
            m = r.json()
            r.close()
            
            if self._compare_ver(m.get('version', '0'), self.version) > 0:
                return m
            return None
        except Exception as e:
            print(f"OTA check error: {e}")
            return None
    
    def update(self):
        manifest = self.check()
        if not manifest:
            print("No updates available")
            return False
        
        new_ver = manifest['version']
        print(f"Updating to {new_ver}...")
        
        files_ok = []
        for f in manifest.get('files', []):
            name = f['name']
            expected_hash = f['sha256']
            
            try:
                # download
                r = urequests.get(f"{self.url}/{name}")
                if r.status_code != 200:
                    print(f"Failed to download {name}")
                    r.close()
                    return False
                
                data = r.content
                r.close()
                
                # verify hash
                if self._sha256(data) != expected_hash.lower():
                    print(f"Hash mismatch for {name}!")
                    return False
                
                # backup old file
                try:
                    os.rename(name, name + '.bak')
                except:
                    pass
                
                # save new file
                with open(name, 'wb') as file:
                    file.write(data)
                
                files_ok.append(name)
                print(f"Updated {name}")
                
            except Exception as e:
                print(f"Error updating {name}: {e}")
                # rollback
                for fname in files_ok:
                    try:
                        os.remove(fname)
                        os.rename(fname + '.bak', fname)
                    except:
                        pass
                return False
        
        # cleanup backups
        for fname in files_ok:
            try:
                os.remove(fname + '.bak')
            except:
                pass
        
        # save version
        with open('version.txt', 'w') as f:
            f.write(new_ver)
        
        print(f"Updated to {new_ver}, rebooting...")
        time.sleep(2)
        machine.reset()
        return True


def get_version():
    try:
        with open('version.txt') as f:
            return f.read().strip()
    except:
        return "1.0.0"
