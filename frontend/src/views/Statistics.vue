<template>
  <my-card>
    <h2>统计信息</h2>
    <div v-if="statistics">
      <p>总车辆数：{{ statistics.total_count }}</p>
      <p>各类别数量：{{ statistics.category_count }}</p>
      <p>长时间停留车辆数：{{ statistics.long_stay_count }}</p>
      <p>过线车辆数：{{ statistics.crossing_count }}</p>
    </div>
    <loading v-else />
  </my-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MyCard from '@/components/MyCard.vue'
import Loading from '@/components/Loading.vue'
import { getStatistics } from '@/api/service'

const statistics = ref(null)
const serviceId = 1 // 实际应由父组件传入

onMounted(async () => {
  const res = await getStatistics(serviceId)
  statistics.value = res.data.statistics
})
</script>