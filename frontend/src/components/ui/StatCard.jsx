import React from 'react';

/**
 * StatCard — hiển thị một chỉ số số học lớn kèm nhãn.
 *
 * Props:
 *   label       {string}    — mô tả ngắn
 *   value       {string}    — giá trị chính
 *   unit        {string}    — đơn vị (ms, %, …)
 *   valueClass  {string}    — class màu áp lên giá trị (tuỳ chọn, mặc định trắng)
 *   highlight   {boolean}   — nếu true, card được đóng khung nổi bật màu xanh
 */
const StatCard = ({
    label,
    value,
    unit,
    valueClass = 'text-white',
    highlight = false,
}) => (
    <div
        className={`bg-slate-900 p-6 rounded-2xl border border-slate-800
                ${highlight ? 'border-blue-900 border-b-2 border-b-blue-600' : ''}`}
    >
        <div className={`text-sm mb-2 ${highlight ? 'text-blue-300' : 'text-slate-400'}`}>
            {label}
        </div>
        <div className={`text-3xl font-heading font-light ${valueClass}`}>
            {value}
            {unit && (
                <span className={`text-lg ml-1 ${highlight ? 'text-blue-400' : 'text-slate-500'}`}>
                    {unit}
                </span>
            )}
        </div>
    </div>
);

export default StatCard;
