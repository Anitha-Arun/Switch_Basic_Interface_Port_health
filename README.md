Here's a detailed and impressive description for your GitHub repository:  

---

# 🚀 Switch Monitoring Tool  

**A powerful, real-time network switch monitoring tool built with Flask.** This tool provides comprehensive insights into switch health, system metrics, and interface performance by executing remote scripts and parsing structured logs.  

## 🔥 Key Features  
- **Real-Time System Metrics:** Monitor system health, CPU utilization, power status, and more.  
- **Interface Port Health Analysis:** Retrieve port status, speed, duplex settings, and log-based port flapping reports.  
- **Inventory Management:** Dynamically fetch switch inventory from a structured configuration file.  
- **Automated Log Parsing:** Extracts relevant data from generated logs for easy visualization.  
- **Interactive Web UI:** Select switches and execute monitoring scripts from a sleek, responsive interface.  
- **Logging & Debugging:** Comprehensive logging for easy troubleshooting and performance tracking.  
- **Reset & Log Management:** Clear logs and reset data with a simple button click.  

## 🛠️ Tech Stack  
- **Flask**: Lightweight Python backend for handling API requests and executing scripts.  
- **Jinja2 (HTML Templates)**: Dynamic UI rendering for displaying fetched data.  
- **Python Subprocess**: Secure execution of monitoring scripts.  
- **Regex Parsing**: Extracts structured information from log files.  
- **Logging Module**: Captures events, errors, and debugging information.  

## 📂 Project Structure  
```
📦 Switch Monitoring Tool
 ├── app.py                      # Main Flask application
 ├── inventory.ini                # Configuration file containing switch IPs
 ├── templates/                   
 │   ├── index3.html              # System monitoring UI
 │   ├── interface.html           # Interface health monitoring UI
 ├── logs/
 │   ├── Switch_monitoring.log    # Application log file
 ├── scripts/
 │   ├── System_healthMetrics.py  # Script to fetch system-level metrics
 │   ├── Interface_Porthealth_Metrics.py # Script for interface port health analysis
```

## 🚀 How It Works  
1. **Hosts Inventory:** The tool reads `inventory.ini` to fetch available switches.  
2. **UI Selection:** Users select a switch and execute a system or interface health check.  
3. **Script Execution:** Flask triggers Python scripts to collect switch data.  
4. **Log Parsing:** Data is extracted from generated logs using regex.  
5. **Real-Time Visualization:** The UI displays results with timestamped reports.  

## 🎯 Use Case  
- Network administrators can use this tool for **quick troubleshooting** and **real-time health checks** of managed switches.  

## 🔧 Installation & Setup  
1. Clone this repository:  
   ```sh
   git clone https://github.com/your-username/switch-monitoring-tool.git
   cd switch-monitoring-tool
   ```  
2. Install dependencies:  
   ```sh
   pip install flask  
   ```  
3. Run the application:  
   ```sh
   python app.py  
   ```  
4. Open in browser:  
   ```
   http://localhost:5000
   ```

## 📝 Contributions  
Feel free to contribute by submitting **pull requests**, **bug reports**, or **feature requests**! 🚀  

