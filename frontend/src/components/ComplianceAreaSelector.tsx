import React, { useState } from 'react';

const COMPLIANCE_AREAS = [
  'Legal',
  'Financial Management and Capacity',
  'Technical Capacity - Award Management',
  'Technical Capacity - Program Management and Subrecipient Oversight',
  'Technical Capacity - Project Management',
  'Transit Asset Management',
  'Satisfactory and Continuing Control',
  'Maintenance',
  'Procurement',
  'Disadvantaged Business Enterprise',
  'Title VI',
  'Americans with Disabilities Act (ADA) - General',
  'ADA - Complementary Paratransit',
  'Equal Employment Opportunity',
  'School Bus',
  'Charter Bus',
  'Drug Free Workplace Act',
  'Drug and Alcohol Program',
  'Section 5307 Program Requirements',
  'Section 5310 Program Requirements',
  'Section 5311 Program Requirements',
  'PTASP',
  'Cybersecurity',
];

interface ComplianceAreaSelectorProps {
  onSubmit: (question: string) => void;
}

export const ComplianceAreaSelector: React.FC<ComplianceAreaSelectorProps> = ({ onSubmit }) => {
  const [selectedArea, setSelectedArea] = useState<string>('');

  const handleSubmit = () => {
    if (selectedArea) {
      const question = `What are the indicators of compliance for ${selectedArea}?`;
      onSubmit(question);
      setSelectedArea(''); // Reset after submit
    }
  };

  return (
    <div className="p-4 bg-white border-b shadow-sm">
      <div className="max-w-4xl mx-auto">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Quick Compliance Area Lookup
        </label>
        <div className="flex gap-2">
          <div className="flex-1">
            <div className="text-sm text-gray-600 mb-1">
              What are the indicators of compliance for...
            </div>
            <select
              value={selectedArea}
              onChange={(e) => setSelectedArea(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            >
              <option value="">Select a compliance area...</option>
              {COMPLIANCE_AREAS.map((area) => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSubmit}
            disabled={!selectedArea}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium mt-6"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
};
