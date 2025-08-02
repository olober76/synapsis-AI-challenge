// Dashboard JavaScript
class Dashboard {
  constructor() {
    this.baseUrl = window.location.origin;
    this.chart = null;
    this.initChart();
    this.startAutoRefresh();
  }

  async apiCall(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("API call failed:", error);
      throw error;
    }
  }

  async loadLiveStats() {
    try {
      const areaId = document.getElementById("areaFilter").value;
      const stats = await this.apiCall(`/api/stats/live?area_id=${areaId}`);

      document.getElementById("liveCountIn").textContent =
        stats.current_count_in || 0;
      document.getElementById("liveCountOut").textContent =
        stats.current_count_out || 0;
      document.getElementById("activeObjects").textContent =
        stats.active_objects || 0;

      // Update status
      const statusIndicator = document.getElementById("statusIndicator");
      const systemStatus = document.getElementById("systemStatus");

      if (stats.last_detection) {
        const lastDetection = new Date(stats.last_detection);
        const now = new Date();
        const timeDiff = (now - lastDetection) / 1000; // seconds

        if (timeDiff < 60) {
          statusIndicator.className = "status-indicator status-online";
          systemStatus.textContent = "Online";
        } else {
          statusIndicator.className = "status-indicator status-offline";
          systemStatus.textContent = "Idle";
        }
      } else {
        statusIndicator.className = "status-indicator status-offline";
        systemStatus.textContent = "No Data";
      }
    } catch (error) {
      console.error("Failed to load live stats:", error);
      document.getElementById("systemStatus").textContent = "Error";
      document.getElementById("statusIndicator").className =
        "status-indicator status-offline";
    }
  }

  async loadHistory() {
    try {
      const startDate = document.getElementById("startDate").value;
      const endDate = document.getElementById("endDate").value;
      const areaId = document.getElementById("areaFilter").value;

      let url = "/api/stats/?";
      const params = new URLSearchParams();

      if (startDate) params.append("start_date", startDate.replace("T", " "));
      if (endDate) params.append("end_date", endDate.replace("T", " "));
      if (areaId) params.append("area_id", areaId);
      params.append("limit", "100");

      url += params.toString();

      const history = await this.apiCall(url);
      this.updateHistoryTable(history);
      this.updateChart(history);
    } catch (error) {
      console.error("Failed to load history:", error);
      this.showError("Failed to load history data");
    }
  }

  updateHistoryTable(data) {
    const tableBody = document.getElementById("historyTableBody");

    if (data.length === 0) {
      tableBody.innerHTML =
        '<tr><td colspan="6" style="text-align: center;">No data found</td></tr>';
      return;
    }

    tableBody.innerHTML = data
      .map(
        (item) => `
            <tr>
                <td>${new Date(item.timestamp).toLocaleString()}</td>
                <td>${item.area_id}</td>
                <td>${item.count_in}</td>
                <td>${item.count_out}</td>
                <td>${item.total_in}</td>
                <td>${item.total_out}</td>
            </tr>
        `
      )
      .join("");
  }

  initChart() {
    const canvas = document.getElementById("countChart");
    const ctx = canvas.getContext("2d");

    // Simple chart implementation (you can replace with Chart.js if needed)
    this.chart = {
      canvas: canvas,
      ctx: ctx,
      data: [],
      draw: function () {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        if (this.data.length === 0) {
          this.ctx.fillStyle = "#666";
          this.ctx.font = "16px Arial";
          this.ctx.textAlign = "center";
          this.ctx.fillText(
            "No data to display",
            this.canvas.width / 2,
            this.canvas.height / 2
          );
          return;
        }

        const padding = 40;
        const chartWidth = this.canvas.width - 2 * padding;
        const chartHeight = this.canvas.height - 2 * padding;

        // Find max values
        const maxIn = Math.max(...this.data.map((d) => d.total_in));
        const maxOut = Math.max(...this.data.map((d) => d.total_out));
        const maxValue = Math.max(maxIn, maxOut);

        if (maxValue === 0) return;

        // Draw lines
        this.ctx.strokeStyle = "#3498db";
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();

        this.data.forEach((point, index) => {
          const x = padding + (index / (this.data.length - 1)) * chartWidth;
          const y =
            padding + chartHeight - (point.total_in / maxValue) * chartHeight;

          if (index === 0) {
            this.ctx.moveTo(x, y);
          } else {
            this.ctx.lineTo(x, y);
          }
        });
        this.ctx.stroke();

        // Draw out line
        this.ctx.strokeStyle = "#e74c3c";
        this.ctx.beginPath();

        this.data.forEach((point, index) => {
          const x = padding + (index / (this.data.length - 1)) * chartWidth;
          const y =
            padding + chartHeight - (point.total_out / maxValue) * chartHeight;

          if (index === 0) {
            this.ctx.moveTo(x, y);
          } else {
            this.ctx.lineTo(x, y);
          }
        });
        this.ctx.stroke();

        // Legend
        this.ctx.fillStyle = "#3498db";
        this.ctx.fillRect(padding, 10, 20, 10);
        this.ctx.fillStyle = "#333";
        this.ctx.font = "12px Arial";
        this.ctx.textAlign = "left";
        this.ctx.fillText("Total In", padding + 25, 20);

        this.ctx.fillStyle = "#e74c3c";
        this.ctx.fillRect(padding + 100, 10, 20, 10);
        this.ctx.fillStyle = "#333";
        this.ctx.fillText("Total Out", padding + 125, 20);
      },
    };
  }

  updateChart(data) {
    this.chart.data = data.reverse(); // Reverse to show chronological order
    this.chart.draw();
  }

  showError(message) {
    // Simple error display (you can enhance this)
    console.error(message);
    alert(`Error: ${message}`);
  }

  startAutoRefresh() {
    // Refresh live stats every 5 seconds
    setInterval(() => {
      this.loadLiveStats();
    }, 5000);

    // Load initial data
    this.loadLiveStats();
    this.loadHistory();

    // Set default date range (last 24 hours)
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    document.getElementById("endDate").value = now.toISOString().slice(0, 16);
    document.getElementById("startDate").value = yesterday
      .toISOString()
      .slice(0, 16);
  }
}

// Global functions for HTML onclick events
function refreshLiveStats() {
  dashboard.loadLiveStats();
}

function loadHistory() {
  dashboard.loadHistory();
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener("DOMContentLoaded", function () {
  dashboard = new Dashboard();
});
