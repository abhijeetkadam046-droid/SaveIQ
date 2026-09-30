/**
 * SaveIQ Visual Analytics & Chart.js Controllers
 */

let categoryChartInstance = null;
let progressChartInstance = null;

function renderCategoryChart(categoryData) {
  const ctx = document.getElementById("categoryChart");
  if (!ctx) return;

  const labels = Object.keys(categoryData);
  const data = Object.values(categoryData);

  const colors = [
    "#6366f1", "#10b981", "#f59e0b", "#06b6d4",
    "#ec4899", "#8b5cf6", "#3b82f6", "#14b8a6"
  ];

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  categoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels.length ? labels : ["No data"],
      datasets: [{
        data: data.length ? data : [1],
        backgroundColor: colors.slice(0, Math.max(1, labels.length)),
        borderWidth: 2,
        borderColor: "rgba(17, 24, 39, 0.8)",
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
            padding: 12,
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              return ` $${val.toLocaleString()}`;
            }
          }
        }
      }
    }
  });
}

function renderProgressBarChart(goals) {
  const ctx = document.getElementById("progressBarChart");
  if (!ctx) return;

  const topGoals = goals.slice(0, 5);
  const labels = topGoals.map(g => g.name.length > 14 ? g.name.substring(0, 14) + '...' : g.name);
  const savedData = topGoals.map(g => g.current_amount);
  const remainingData = topGoals.map(g => g.remaining_amount);

  if (progressChartInstance) {
    progressChartInstance.destroy();
  }

  progressChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Current Saved ($)",
          data: savedData,
          backgroundColor: "#10b981",
          borderRadius: 6
        },
        {
          label: "Remaining Gap ($)",
          data: remainingData,
          backgroundColor: "rgba(99, 102, 241, 0.25)",
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { color: "#94a3b8", font: { size: 10 } }
        },
        y: {
          stacked: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            callback: value => `$${value}`
          }
        }
      },
      plugins: {
        legend: {
          position: "top",
          labels: { color: "#94a3b8", usePointStyle: true }
        }
      }
    }
  });
}
