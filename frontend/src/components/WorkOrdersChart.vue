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
          type: 'bar',
          data: props.data,
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.dataset.label || ''}: ${context.raw}`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  stepSize: 1
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