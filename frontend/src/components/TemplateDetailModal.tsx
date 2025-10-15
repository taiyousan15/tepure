/**
 * Template detail modal component
 */
import React, { useEffect, useState } from 'react';
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
  figma_file_key: string;
  figma_node_id: string;
  fields: Field[];
}

interface Props {
  templateId: string;
  isOpen: boolean;
  onClose: () => void;
  onUse: (templateId: string) => void;
}

export default function TemplateDetailModal({ templateId, isOpen, onClose, onUse }: Props) {
  const [template, setTemplate] = useState<TemplateDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && templateId) {
      fetchTemplateDetail();
    }
  }, [isOpen, templateId]);

  const fetchTemplateDetail = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/v1/templates/${templateId}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error('テンプレート詳細の取得に失敗しました');
      }

      const data = await response.json();
      setTemplate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">テンプレート詳細</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* コンテンツ */}
        <div className="p-6">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-600 border-r-transparent"></div>
              <p className="mt-2 text-gray-600">読み込み中...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {template && !loading && (
            <div className="space-y-6">
              {/* プレビュー画像 */}
              {template.preview_url && (
                <div className="aspect-video bg-gray-200 rounded-lg overflow-hidden">
                  <img
                    src={template.preview_url}
                    alt={template.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* 基本情報 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">テンプレート名</h3>
                  <p className="mt-1 text-lg font-semibold text-gray-900">{template.name}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">カテゴリ</h3>
                  <p className="mt-1">
                    <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                      {template.category}
                    </span>
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Figma File ID</h3>
                  <p className="mt-1 text-sm text-gray-700 font-mono bg-gray-50 p-2 rounded">
                    {template.figma_file_key}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Figma Node ID</h3>
                  <p className="mt-1 text-sm text-gray-700 font-mono bg-gray-50 p-2 rounded">
                    {template.figma_node_id || 'なし'}
                  </p>
                </div>
              </div>

              {/* フィールド一覧 */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  入力フィールド ({template.fields?.length || 0}個)
                </h3>
                {template.fields && template.fields.length > 0 ? (
                  <div className="space-y-2">
                    {template.fields.map((field) => (
                      <div
                        key={field.id}
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                                {field.node_id}
                              </span>
                              {field.required && (
                                <span className="text-xs text-red-600 font-medium">必須</span>
                              )}
                            </div>
                            <p className="mt-1 text-sm text-gray-600">
                              レイヤー名: {field.layer_name || 'なし'}
                            </p>
                          </div>
                          <div className="text-right">
                            <span className="text-xs text-gray-500 uppercase">{field.type}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8 bg-gray-50 rounded-lg">
                    フィールド情報がありません
                  </p>
                )}
              </div>

              {/* アクションボタン */}
              <div className="flex space-x-4 pt-4 border-t">
                <button
                  onClick={() => {
                    onUse(template.id);
                    onClose();
                  }}
                  className="flex-1 bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700"
                >
                  このテンプレートを使用する
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
                >
                  閉じる
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
