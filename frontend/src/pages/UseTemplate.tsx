/**
 * Template usage page - Input form for template fields
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAuthHeaders } from '../utils/auth';

interface Field {
  id: string;
  node_id: string;
  type: string;
  layer_name: string;
  default_value: string;
  required: boolean;
}

interface TemplateDetail {
  id: string;
  name: string;
  category: string;
  preview_url: string;
  fields: Field[];
}

export default function UseTemplate() {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();

  const [template, setTemplate] = useState<TemplateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // フィールド入力値
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});

  useEffect(() => {
    if (templateId) {
      fetchTemplateDetail();
    }
  }, [templateId]);

  const fetchTemplateDetail = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/v1/templates/${templateId}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('テンプレート情報の取得に失敗しました');
      }

      const data = await response.json();
      setTemplate(data);

      // デフォルト値を設定
      const defaults: Record<string, string> = {};
      data.fields?.forEach((field: Field) => {
        defaults[field.node_id] = field.default_value || '';
      });
      setFieldValues(defaults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (nodeId: string, value: string) => {
    setFieldValues({
      ...fieldValues,
      [nodeId]: value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      // ジョブ実行APIを呼び出す
      const response = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template_id: templateId,
          input_data: fieldValues,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'ジョブ作成に失敗しました');
      }

      const data = await response.json();

      // 成功メッセージを表示
      alert(`✅ ジョブ作成成功！\n\nJob ID: ${data.job_id}\nテンプレート: ${data.template_name}\n\n${data.message}`);

      // テンプレート一覧に戻る
      navigate('/templates');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
        <p className="mt-2 text-gray-600">読み込み中...</p>
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error || 'テンプレートが見つかりませんでした'}</p>
        </div>
        <button
          onClick={() => navigate('/templates')}
          className="mt-4 text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ← テンプレート一覧に戻る
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* ヘッダー */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/templates')}
          className="text-indigo-600 hover:text-indigo-800 font-medium mb-4"
        >
          ← テンプレート一覧に戻る
        </button>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">テンプレートを使用</h2>
        <p className="text-gray-600">テンプレート: {template.name}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左側: プレビュー */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="font-semibold text-gray-900 mb-4">プレビュー</h3>
          {template.preview_url ? (
            <img
              src={template.preview_url}
              alt={template.name}
              className="w-full rounded-lg border border-gray-200"
            />
          ) : (
            <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">プレビュー画像なし</p>
            </div>
          )}

          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-blue-900 text-sm mb-2">📌 使い方</h4>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>右側のフォームに内容を入力</li>
              <li>「テンプレートを生成」をクリック</li>
              <li>Figmaプラグインで確認・書き出し</li>
            </ol>
          </div>
        </div>

        {/* 右側: 入力フォーム */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="font-semibold text-gray-900 mb-4">
            入力フィールド ({template.fields?.length || 0}個)
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            {template.fields && template.fields.length > 0 ? (
              template.fields.map((field) => (
                <div key={field.id}>
                  <label htmlFor={field.node_id} className="block text-sm font-medium text-gray-700 mb-1">
                    {field.layer_name || field.node_id}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type="text"
                    id={field.node_id}
                    value={fieldValues[field.node_id] || ''}
                    onChange={(e) => handleFieldChange(field.node_id, e.target.value)}
                    required={field.required}
                    placeholder={`例: ${field.default_value || '入力してください'}`}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    レイヤー: <span className="font-mono">{field.node_id}</span>
                  </p>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                フィールド情報がありません
              </p>
            )}

            <div className="pt-4 border-t">
              <button
                type="submit"
                disabled={submitting || !template.fields || template.fields.length === 0}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? '生成中...' : '✨ テンプレートを生成'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}
    </div>
  );
}
