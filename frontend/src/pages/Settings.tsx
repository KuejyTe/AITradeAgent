import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Switch, Tabs, message, InputNumber } from 'antd';
import { SafetyOutlined, ApiOutlined, SettingOutlined, BellOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;
const { TextArea } = Input;

interface APIKeys {
  api_key: string;
  secret_key: string;
  passphrase: string;
}

interface SystemConfig {
  default_trade_amount: number;
  max_position_size: number;
  risk_percentage: number;
  log_level: string;
}

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [apiForm] = Form.useForm();
  const [tradingForm] = Form.useForm();
  const [apiConfigured, setApiConfigured] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // 加载系统配置
      const systemRes = await fetch('/api/config/system');
      const systemData = await systemRes.json();
      
      tradingForm.setFieldsValue({
        default_trade_amount: systemData.default_trade_amount,
        max_position_size: systemData.max_position_size,
        risk_percentage: systemData.risk_percentage * 100, // 转换为百分比
      });

      // 检查API密钥状态
      const apiStatusRes = await fetch('/api/config/api-keys/status');
      const apiStatus = await apiStatusRes.json();
      setApiConfigured(apiStatus.configured);
      
    } catch (error) {
      message.error('加载配置失败');
    }
  };

  const handleSaveAPIKeys = async (values: APIKeys) => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        message.success('API密钥保存成功');
        setApiConfigured(true);
        apiForm.resetFields();
      } else {
        const error = await response.json();
        message.error(error.detail || 'API密钥保存失败');
      }
    } catch (error) {
      message.error('保存失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/api-keys/test', {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        message.success(`连接测试成功！延迟：${data.latency_ms}ms`);
      } else {
        message.error('连接测试失败');
      }
    } catch (error) {
      message.error('测试失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTradingConfig = async (values: any) => {
    setLoading(true);
    try {
      const config = {
        ...values,
        risk_percentage: values.risk_percentage / 100, // 转换回小数
      };

      const response = await fetch('/api/config/system', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        message.success('交易配置保存成功');
      } else {
        message.error('保存失败');
      }
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
<h1>系统设置</h1>

  <Tabs defaultActiveKey="api">
    {/* API配置 */}
    <TabPanetab={
        <span>
          <ApiOutlined />
          API配置
        </span>
      }
      key="api"
    >
      <Card>
        <div style={{ marginBottom: 16 }}>
          {apiConfigured && (
            <div style={{ color: '#52c41a', marginBottom: 16 }}>
              ✓ API密钥已配置
            </div>
          )}
          <p style={{ color: '#666' }}>
            配置欧易(OKX)交易所API密钥。密钥将被加密存储，请确保密钥权限仅包含交易和查询。
          </p>
        </div>

        <Form
          form={apiForm}layout="vertical"
onFinish={handleSaveAPIKeys}
>
<Form.Item
label="API Key"
name="api_key"
rules={[{ required: true, message: '请输入API Key' }]}
>
<Input.Password placeholder="输入API Key" />
</Form.Item>

          <Form.Item
            label="Secret Key"
            name="secret_key"
            rules={[{ required: true, message: '请输入Secret Key' }]}
          >
            <Input.Password placeholder="输入Secret Key" />
          </Form.Item>

          <Form.Item
            label="Passphrase"
            name="passphrase"
            rules={[{ required: true, message: '请输入Passphrase' }]}
          >
            <Input.Password placeholder="输入Passphrase" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存API密钥
            </Button>
            <Button
              style={{ marginLeft: 8 }}
              onClick={handleTestConnection}
              loading={loading}
              disabled={!apiConfigured}
            >
              测试连接
            </Button>
          </Form.Item>
        </Form>

        <div style={{ marginTop: 24, padding: 16, background: '#f0f0f0', borderRadius: 4 }}>
          <h4>安全提示：</h4>
          <ul>
            <li>请确保API密钥仅用于交易和查询，不要授予提现权限</li>
            <li>建议使用IP白名单限制API访问</li>
            <li>定期更换API密钥</li>
            <li>不要将API密钥分享给他人</li>
          </ul>
        </div>
      </Card>
    </TabPane>

    {/* 交易配置 */}
    <TabPane
      tab={
        <span>
          <SettingOutlined />
          交易配置
        </span>
      }
      key="trading"
    >
      <Card>
        <Form
          form={tradingForm}
          layout="vertical"
          onFinish={handleSaveTradingConfig}
        >
          <Form.Item
            label="默认交易金额 (USDT)"
            name="default_trade_amount"
            rules={[{ required: true, message: '请输入默认交易金额' }]}
          >
            <InputNumber
              min={10}
              max={100000}
              style={{ width: '100%' }}
              placeholder="100"
            />
          </Form.Item>

          <Form.Item
            label="最大持仓限制 (USDT)"
            name="max_position_size"
            rules={[{ required: true, message: '请输入最大持仓限制' }]}
          >
            <InputNumber
              min={100}
              max={1000000}
              style={{ width: '100%' }}
              placeholder="10000"
            />
          </Form.Item>

          <Form.Item
            label="风险百分比 (%)"
            name="risk_percentage"
            rules={[{ required: true, message: '请输入风险百分比' }]}
            tooltip="单笔交易最大风险占总资金的百分比"
          >
            <InputNumber
              min={0.1}
              max={10}
              step={0.1}
              style={{ width: '100%'}}
placeholder="2"
/>
</Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </TabPane>

    {/* 通知配置 */}
    <TabPane
      tab={<span>
          <BellOutlined />
          通知配置
        </span>
      }
      key="notifications"
    >
      <Card>
        <Form layout="vertical">
          <Form.Item label="价格告警">
            <Switch defaultChecked />
            <span style={{ marginLeft: 8 }}>启用价格变动告警</span>
          </Form.Item>

          <Form.Item label="订单通知">
            <Switch defaultChecked />
            <span style={{ marginLeft: 8 }}>订单成交时发送通知</span>
          </Form.Item>

          <Form.Item label="邮件通知">
            <Input placeholder="your.email@example.com" />
          </Form.Item>

          <Form.Item label="Telegram Bot Token">
            <Input.Password placeholder="输入Telegram Bot Token（可选）" />
          </Form.Item>

          <Form.Item label="Telegram Chat ID">
            <Input placeholder="输入Chat ID（可选）" />
          </Form.Item>

          <Form.Item>
            <Button type="primary">保存通知配置</Button>
          </Form.Item>
        </Form>
      </Card>
    </TabPane>
  </Tabs>
</div>
);
};

export default Settings;
