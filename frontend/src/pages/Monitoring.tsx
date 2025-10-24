import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space } from 'antd';
import {
CheckCircleOutlined,
CloseCircleOutlined,
SyncOutlined,
ReloadOutlined
} from '@ant-design/icons';
import { Line } from '@ant-design/charts';

interface SystemStatus {
status: string;
uptime_seconds: number;
checks: {
database: boolean;
redis: boolean;
okx_api: boolean;
websocket: boolean;
};
}

const Monitoring: React.FC = () => {
const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
const [loading, setLoading] = useState(false);
const [performanceData, setPerformanceData] = useState([]);

useEffect(() => {
loadSystemStatus();
const interval = setInterval(loadSystemStatus, 10000); // 每10秒刷新
return () => clearInterval(interval);
}, []);

const loadSystemStatus = async () => {
setLoading(true);
try {
const response = await fetch('/api/health/detailed');
const data = await response.json();
setSystemStatus(data);
} catch (error) {
console.error('Failed to load system status:', error);
} finally {
setLoading(false);
}
};

const formatUptime = (seconds: number) => {
const hours = Math.floor(seconds / 3600);
const minutes = Math.floor((seconds % 3600) / 60);
return ${hours}小时 ${minutes}分钟;
};

const statusIcon = (status: boolean) => {
return status ? (
<CheckCircleOutlined style={{ color: '#52c41a

', fontSize: 24 }} />
) : (
<CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 24 }} />
);
};

return (
<div style={{ padding: '24px' }}>
<div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
<h1>系统监控</h1>
<Button
icon={<ReloadOutlined />}
onClick={loadSystemStatus}
loading={loading}
>
刷新
</Button>
</div>

  {/* 系统状态卡片 */}
  <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
    <Col span={6}>
      <Card>
        <Statistic
          title="系统状态"
          value={systemStatus?.status || 'unknown'}
          valueStyle={{
            color: systemStatus?.status === 'healthy' ? '#3f8600' : '#cf1322'
          }}
          prefix={
            systemStatus?.status === 'healthy' ? (
              <CheckCircleOutlined />
            ) : (
              <CloseCircleOutlined />
            )
          }
        />
      </Card>
    </Col>
    <Col span={6}>
      <Card>
        <Statistic
          title="运行时间"
          value={systemStatus ? formatUptime(systemStatus.uptime_seconds) : '-'}
          prefix={<SyncOutlined spin />}
        />
      </Card>
    </Col>
    <Col span={6}>
      <Card>
        <Statistic
          title="今日交易"
          value={156}
          suffix="笔"
        />
      </Card>
    </Col>
    <Col span={6}>
      <Card>
        <Statistic
          title="活跃订单"
          value={8}
          suffix="个"
        />
      </Card>
    </Col>
  </Row>

  {/* 组件状态 */}
  <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
    <Col span={12}>
      <Card title="组件状态" loading={loading}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>数据库</span>
            {systemStatus && statusIcon(systemStatus.checks.database)}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Redis缓存</span>
            {
systemStatus && statusIcon(systemStatus.checks.redis)}
</div>
<div style={{ display: 'flex', justify

Content: 'space-between', alignItems: 'center' }}>
<span>OKX API</span>
{systemStatus && statusIcon(systemStatus.checks.okx_api)}
</div>
<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
<span>WebSocket</span>
{systemStatus && statusIcon(systemStatus.checks.websocket)}
</div>
</Space>
</Card>
</Col>

    <Col span={12}>
      <Card title="性能指标">
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="API响应时间"
              value={125}
              suffix="ms"
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="请求QPS"
              value={45}
              suffix="/s"
            />
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Statistic
              title="错误率"
              value={0.12}
              suffix="%"
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="WebSocket连接"
              value={12}
              suffix="个"
            />
          </Col>
        </Row>
      </Card>
    </Col>
  </Row>

  {/*最近错误 */}
<Card title="最近错误" style={{ marginBottom: 16 }}>
<Table
dataSource={[
{
key: '1',
time: '2025-10-23 14:30:15',
level: 'ERROR',
module: 'trading',
message: '订单提交失败: 网络超时'
},
{
key: '2',
time: '2025-10-23 14:28:42',
level: 'WARNING',
module: 'strategy',
message: '策略信号强度低于阈值'
}
]}
columns={[
{
title: '时间',
dataIndex: 'time',
key: 'time'
},
{
title: '级别',
dataIndex: 'level',
key: 'level',
render: (level: string) => (
<Tag color={level === 'ERROR' ? 'red' : 'orange'}>
{level}
</Tag>
)
},
{
title: '模块',
dataIndex: 'module',
key: 'module'
},
{
title: '消息',
dataIndex: 'message',
key: 'message'
}
]}
pagination={false}
size="small"
/>
</Card>
</div>
);
};

export default Monitoring;




