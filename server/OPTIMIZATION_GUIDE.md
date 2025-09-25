# Raspberry Pi Zero 2 W Optimization Guide

## Memory Crisis Solutions for Video Streaming

Your Pi Zero 2 W crashed because it has only **512MB RAM** and the camera/encoder uses significant memory. Here are optimization strategies:

## 1. **Use the Optimized Scripts**

### Original (causes crashes):
- Resolution: 1280x720
- Bitrate: 1Mbps  
- Buffers: 4 (default)
- Memory usage: ~200-300MB

### Optimized version (`capture_stream.py`):
- Resolution: 640x480
- Bitrate: 500kbps
- Buffers: 2 (minimal)
- Memory monitoring
- Memory usage: ~100-150MB

### Ultra-lightweight (`lightweight_stream.py`):
- Resolution: 480x320
- Bitrate: 300kbps
- Frame rate: 15fps
- Buffers: 2 (minimal)
- Aggressive garbage collection
- Memory usage: ~50-80MB

## 2. **System-Level Optimizations**

### A. Increase GPU Memory Split
```bash
sudo raspi-config
# Go to: Advanced Options > Memory Split
# Set to: 128 (gives more memory to GPU for camera)
sudo reboot
```

### B. Reduce System Services
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-ap
sudo systemctl disable triggerhappy

# Stop GUI if not needed
sudo systemctl set-default multi-user.target
```

### C. Add Swap File (Emergency memory)
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change: CONF_SWAPSIZE=512
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### D. Memory Management Settings
```bash
# Add to /boot/config.txt
echo "gpu_mem=128" | sudo tee -a /boot/config.txt
echo "start_file=start_x.elf" | sudo tee -a /boot/config.txt
echo "fixup_file=fixup_x.dat" | sudo tee -a /boot/config.txt
```

## 3. **Runtime Optimizations**

### Monitor Memory Before Starting:
```bash
free -h
# Should show at least 200MB available
```

### Kill Unnecessary Processes:
```bash
# Check what's running
ps aux --sort=-%mem | head -10

# Kill heavy processes if needed
sudo pkill chromium-browser
sudo pkill firefox
```

### Use Process Priorities:
```bash
# Run with higher priority
sudo nice -n -10 python3 lightweight_stream.py
```

## 4. **Alternative Approaches**

### A. **MJPEG Streaming** (Much lighter):
- No H.264 encoding (CPU intensive)
- Lower compression but less memory
- Good for local networks

### B. **Reduce Frame Rate**:
```python
# In camera config:
"FrameRate": 10  # Instead of 30fps
```

### C. **Use Hardware-Optimized Libraries**:
```bash
# Install optimized libraries
sudo apt install python3-opencv
pip3 install --no-cache-dir picamera2
```

## 5. **Monitoring Commands**

### Check Memory Usage:
```bash
# Real-time memory monitoring
watch -n 2 'free -h && echo "--- GPU Memory ---" && vcgencmd get_mem gpu && vcgencmd get_mem arm'
```

### Check Temperature (thermal throttling):
```bash
vcgencmd measure_temp
# Should be < 80°C
```

### Check for Low Voltage:
```bash
vcgencmd get_throttled
# 0x0 = OK, anything else = power issues
```

## 6. **Recommended Settings by Use Case**

### **Stable Long-term Streaming**:
- Use `lightweight_stream.py`
- 480x320 resolution
- 300kbps bitrate
- Add swap file

### **Better Quality (Short sessions)**:
- Use optimized `capture_stream.py`
- 640x480 resolution  
- 500kbps bitrate
- Monitor memory actively

### **Maximum Compatibility**:
- MJPEG instead of H.264
- 320x240 resolution
- 150kbps bitrate

## 7. **Emergency Recovery**

If Pi keeps crashing:
1. **Boot in safe mode**: Add `init=/bin/bash` to cmdline.txt
2. **Reduce GPU memory**: Set `gpu_mem=64` in config.txt
3. **Add swap**: Enable 1GB swap file
4. **Check SD card**: Use `fsck` to check for corruption

## 8. **Testing Checklist**

Before running streaming:
- [ ] Available RAM > 150MB
- [ ] Temperature < 70°C  
- [ ] No throttling warnings
- [ ] GPU memory = 128MB
- [ ] Swap enabled
- [ ] Only essential processes running

Use these optimizations and your Pi Zero 2 W should handle streaming much more reliably!