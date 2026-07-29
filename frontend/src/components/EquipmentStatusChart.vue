<template>
    <canvas ref="chartCanvas"></canvas>
  </template>
  
  <script>
  import { ref, onMounted, watch } from 'vue';
  import { Chart, registerables } from 'chart.js';
  Chart.register(...registerables);
  
  export default {
    props: {
      data: {
        type: Object,
        required: true,
        default: () => ({
          labels: [],
          datasets: []
        })
      }
    },
    setup(props) {
      const chartCanvas = ref(null);
      let chartInstance = null;
  
      onMounted(() => {
        renderChart();
      });
  
      watch(() => props.data, () => {
        if (chartInstance) {
          chartInstance.destroy();
        }
        renderChart();
      }, { deep: true });
  
      const renderChart = () => {
        const ctx = chartCanvas.value.getContext('2d');
        chartInstance = new Chart(ctx, {
          type: 'pie',
          data: props.data,
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.label || '';
                    const value = context.raw || 0;
                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                    const percentage = Math.round((value / total) * 100);
                    return `${label}: ${value} (${percentage}%)`;
                  }
                }
              }
            }
          }
        });
      };
  
      return {
        chartCanvas
      };
    }
  };
  </script>