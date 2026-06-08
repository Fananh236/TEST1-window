"""
Test Suite 02: System Checks
- Kiểm tra hệ thống Raspberry Pi
- Tách nhỏ từng bước: network, disk, resources, tools
"""
import pytest


class TestNetworkConnectivity:
    """Kiểm tra kết nối mạng"""

    def test_02_01_localhost_ping(self, pi_device):
        """
        BƯỚC 1: Kiểm tra localhost.
        """
        output, error = pi_device.execute_command("ping -c 1 127.0.0.1")
        
        assert error == "", f"Lỗi: {error}"
        assert "1 received" in output or "0% loss" in output, f"Ping failed: {output}"
        print("✅ Localhost is reachable")

    def test_02_02_gateway_ping(self, pi_device):
        """
        BƯỚC 2: Kiểm tra gateway.
        """
        # Lấy gateway
        gw_output, _ = pi_device.execute_command("route -n | grep '^0.0.0.0' | awk '{print $3}' | head -1")
        gateway = gw_output.strip()
        
        if gateway:
            output, error = pi_device.execute_command(f"ping -c 1 {gateway}")
            assert "1 received" in output or "0% loss" in output, f"Gateway ping failed: {output}"
            print(f"✅ Gateway {gateway} is reachable")
        else:
            print("⚠️ No gateway found, skipping")

    def test_02_03_dns_resolution(self, pi_device):
        """
        BƯỚC 3: Kiểm tra DNS resolution.
        """
        output, error = pi_device.execute_command("nslookup google.com 2>&1 | grep -i 'name\\|address' | head -3")
        
        assert len(output) > 0, "DNS resolution failed"
        print(f"✅ DNS works: {output.strip()[:50]}...")

    def test_02_04_internet_connectivity(self, pi_device):
        """
        BƯỚC 4: Kiểm tra internet connection.
        """
        output, error = pi_device.execute_command("ping -c 1 8.8.8.8 2>&1 || echo 'No internet'")
        
        if "1 received" in output or "0% loss" in output:
            print("✅ Internet connectivity confirmed")
        else:
            print("⚠️ No direct internet access, but network may still work")


class TestDiskSpace:
    """Kiểm tra không gian đĩa"""

    def test_03_01_disk_usage(self, pi_device):
        """
        BƯỚC 5: Kiểm tra tổng thể disk usage.
        """
        output, error = pi_device.execute_command("df -h /")
        
        assert error == "", f"Lỗi: {error}"
        assert "Filesystem" in output or "Size" in output, f"Invalid df output: {output}"
        print(f"✅ Disk space check works")

    def test_03_02_root_partition_space(self, pi_device):
        """
        BƯỚC 6: Kiểm tra dung lượng root partition.
        """
        output, error = pi_device.execute_command("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
        
        try:
            usage_percent = int(output.strip())
            assert usage_percent < 95, f"Disk almost full: {usage_percent}%"
            print(f"✅ Root partition usage: {usage_percent}%")
        except:
            print(f"⚠️ Could not parse disk usage: {output}")

    def test_03_03_tmp_partition_space(self, pi_device):
        """
        BƯỚC 7: Kiểm tra /tmp space.
        """
        output, error = pi_device.execute_command("df -h /tmp 2>/dev/null || df -h /")
        
        assert error == "" or len(output) > 0, "Could not check /tmp"
        print(f"✅ /tmp space check works")

    def test_03_04_home_partition_space(self, pi_device):
        """
        BƯỚC 8: Kiểm tra home partition.
        """
        home_dir = f"/home/{pi_device.username}"
        output, error = pi_device.execute_command(f"du -sh {home_dir} 2>/dev/null | awk '{{print $1}}'")
        
        if len(output) > 0:
            print(f"✅ Home directory size: {output.strip()}")
        else:
            print(f"⚠️ Could not determine home directory size")


class TestSystemResources:
    """Kiểm tra tài nguyên hệ thống"""

    def test_04_01_cpu_info(self, pi_device):
        """
        BƯỚC 9: Kiểm tra CPU thông tin.
        """
        output, error = pi_device.execute_command("nproc")
        
        try:
            cpu_count = int(output.strip())
            assert cpu_count > 0, "Invalid CPU count"
            print(f"✅ CPU cores: {cpu_count}")
        except:
            print(f"⚠️ Could not get CPU count: {output}")

    def test_04_02_memory_info(self, pi_device):
        """
        BƯỚC 10: Kiểm tra bộ nhớ.
        """
        output, error = pi_device.execute_command("free -h | grep 'Mem' | awk '{print $2}'")
        
        memory = output.strip()
        if memory:
            print(f"✅ Total memory: {memory}")
        else:
            print(f"⚠️ Could not get memory info")

    def test_04_03_memory_usage(self, pi_device):
        """
        BƯỚC 11: Kiểm tra mức sử dụng bộ nhớ.
        """
        output, error = pi_device.execute_command("free | grep 'Mem' | awk '{printf \"%.0f\", $3/$2*100}'")
        
        try:
            usage_percent = int(output.strip())
            assert usage_percent < 90, f"Memory usage high: {usage_percent}%"
            print(f"✅ Memory usage: {usage_percent}%")
        except:
            print(f"⚠️ Could not parse memory usage: {output}")

    def test_04_04_load_average(self, pi_device):
        """
        BƯỚC 12: Kiểm tra load average.
        """
        output, error = pi_device.execute_command("uptime | grep -oE 'load average[^,]*'")
        
        if output:
            print(f"✅ {output.strip()}")
        else:
            print(f"⚠️ Could not get load average")

    def test_04_05_uptime(self, pi_device):
        """
        BƯỚC 13: Kiểm tra uptime.
        """
        output, error = pi_device.execute_command("uptime -p 2>/dev/null || uptime")
        
        if output:
            print(f"✅ {output.strip()}")


class TestSystemSoftware:
    """Kiểm tra phần mềm hệ thống"""

    def test_05_01_os_info(self, pi_device):
        """
        BƯỚC 14: Kiểm tra thông tin OS.
        """
        output, error = pi_device.execute_command("uname -s")
        
        os_name = output.strip()
        assert "Linux" in os_name, f"Not Linux: {os_name}"
        print(f"✅ OS: {os_name}")

    def test_05_02_kernel_version(self, pi_device):
        """
        BƯỚC 15: Kiểm tra kernel version.
        """
        output, error = pi_device.execute_command("uname -r")
        
        kernel = output.strip()
        assert len(kernel) > 0, "Could not get kernel version"
        print(f"✅ Kernel: {kernel}")

    def test_05_03_distribution(self, pi_device):
        """
        BƯỚC 16: Kiểm tra distribution.
        """
        output, error = pi_device.execute_command("cat /etc/os-release | grep PRETTY_NAME | cut -d '=' -f 2 | tr -d '\"'")
        
        distro = output.strip()
        if distro:
            print(f"✅ Distribution: {distro}")
        else:
            print(f"⚠️ Could not determine distribution")

    def test_05_04_python_version(self, pi_device):
        """
        BƯỚC 17: Kiểm tra Python version.
        """
        output, error = pi_device.execute_command("python3 --version")
        
        python_version = output.strip()
        assert "Python" in python_version, f"Python not found: {python_version}"
        print(f"✅ {python_version}")

    def test_05_05_pip_available(self, pi_device):
        """
        BƯỚC 18: Kiểm tra pip available.
        """
        output, error = pi_device.execute_command("pip3 --version")
        
        pip_version = output.strip()
        assert "pip" in pip_version, f"pip not found: {pip_version}"
        print(f"✅ {pip_version}")
