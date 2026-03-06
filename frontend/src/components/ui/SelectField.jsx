import React from 'react';

/**
 * SelectField — tái sử dụng cho mọi dropdown lựa chọn trong sidebar.
 *
 * Props:
 *   label   {string}                  — nhãn hiển thị bên cạnh icon
 *   icon    {ReactNode}               — icon từ lucide-react
 *   value   {string}                  — giá trị hiện tại (tag hoặc string)
 *   options {string[]|{label,tag}[]}  — danh sách lựa chọn
 *   onChange {Function}               — handler khi người dùng thay đổi
 */
const SelectField = ({ label, icon: Icon, value, options, onChange }) => {
    // Normalise: string → { label: string, tag: string }
    const normalised = options.map((opt) =>
        typeof opt === 'string' ? { label: opt, tag: opt } : opt
    );

    return (
        <div className="space-y-1.5">
            <label className="text-xs text-slate-400 font-medium flex items-center gap-2">
                {Icon && <Icon size={14} />}
                {label}
            </label>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-300 text-sm rounded-lg p-2
                   focus:ring-1 focus:ring-blue-500 outline-none transition-all cursor-pointer"
            >
                {normalised.map(({ label: optLabel, tag }) => (
                    <option key={tag} value={tag}>{optLabel}</option>
                ))}
            </select>
        </div>
    );
};

export default SelectField;
