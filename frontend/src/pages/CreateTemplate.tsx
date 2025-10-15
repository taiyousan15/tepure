/**
 * Template creation page
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthHeaders } from '../utils/auth';

export default function CreateTemplate() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    category: 'LP',
    figma_file_id: '',
    figma_node_id: '',
    thumbnail_url: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/v1/templates', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'テンプレート作成に失敗しました');
      }

      const data = await response.json();
      alert(`テンプレート作成成功！ID: ${data.id}`);
      navigate('/templates');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => navigate('/templates')}
          className="text-indigo-600 hover:text-indigo-800 font-medium"
        >
          ← テンプレート一覧に戻る
        </button>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">新規テンプレート登録</h2>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* テンプレート名 */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              テンプレート名 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              placeholder="LP-ヒーロー左画像"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* カテゴリ */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              カテゴリ <span className="text-red-500">*</span>
            </label>
            <select
              id="category"
              name="category"
              required
              value={formData.category}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="LP">LP (ランディングページ)</option>
              <option value="Banner">Banner (バナー広告)</option>
              <option value="SNS">SNS (SNS投稿)</option>
              <option value="WebApp">WebApp (Webアプリ)</option>
            </select>
          </div>

          {/* Figma File ID */}
          <div>
            <label htmlFor="figma_file_id" className="block text-sm font-medium text-gray-700 mb-2">
              Figma File ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="figma_file_id"
              name="figma_file_id"
              required
              value={formData.figma_file_id}
              onChange={handleChange}
              placeholder="abc123xyz..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              FigmaファイルのURLから取得: figma.com/file/
              <span className="font-mono bg-gray-100 px-1">FILE_ID</span>/...
            </p>
          </div>

          {/* Figma Node ID */}
          <div>
            <label htmlFor="figma_node_id" className="block text-sm font-medium text-gray-700 mb-2">
              Figma Node ID (任意)
            </label>
            <input
              type="text"
              id="figma_node_id"
              name="figma_node_id"
              value={formData.figma_node_id}
              onChange={handleChange}
              placeholder="123:456"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              特定のFrame/Componentを指定する場合のみ入力
            </p>
          </div>

          {/* サムネイルURL */}
          <div>
            <label htmlFor="thumbnail_url" className="block text-sm font-medium text-gray-700 mb-2">
              サムネイルURL (任意)
            </label>
            <input
              type="url"
              id="thumbnail_url"
              name="thumbnail_url"
              value={formData.thumbnail_url}
              onChange={handleChange}
              placeholder="https://example.com/thumbnail.png"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <p className="mt-1 text-sm text-gray-500">
              テンプレートのプレビュー画像URL
            </p>
          </div>

          {/* ボタン */}
          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-indigo-600 text-white py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '登録中...' : 'テンプレートを登録'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/templates')}
              disabled={loading}
              className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              キャンセル
            </button>
          </div>
        </form>
      </div>

      {/* 使い方ガイド */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">📚 テンプレート登録ガイド</h3>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Figmaでテンプレートを作成</li>
          <li>テキストレイヤーに分かりやすい名前を付ける（例: HEAD_TITLE, SUB_TITLE）</li>
          <li>FigmaファイルのURLからFile IDをコピー</li>
          <li>このフォームでテンプレート情報を登録</li>
          <li>Figmaプラグインで「テンプレート情報を取得」してフィールドを確認</li>
        </ol>
      </div>
    </div>
  );
}
