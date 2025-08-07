import React from 'react';
import { BookOpen, Users, Gamepad2, Lightbulb, Target, Brain, Puzzle, Zap, GraduationCap } from 'lucide-react';

const pedagogyOptions = [
  {
    id: 'inquiry-based',
    name: 'Inquiry-Based',
    description: 'Students learn through questioning and exploration',
    icon: Lightbulb,
    color: 'bg-yellow-100 border-yellow-300 text-yellow-800'
  },
  {
    id: 'project-based',
    name: 'Project-Based',
    description: 'Learning through real-world projects and applications',
    icon: Target,
    color: 'bg-blue-100 border-blue-300 text-blue-800'
  },
  {
    id: 'collaborative',
    name: 'Collaborative',
    description: 'Group work and peer-to-peer learning',
    icon: Users,
    color: 'bg-green-100 border-green-300 text-green-800'
  },
  {
    id: 'game-based',
    name: 'Game-Based',
    description: 'Learning through games and interactive challenges',
    icon: Gamepad2,
    color: 'bg-purple-100 border-purple-300 text-purple-800'
  },
  {
    id: 'traditional',
    name: 'Traditional',
    description: 'Structured lecture-based teaching approach',
    icon: BookOpen,
    color: 'bg-gray-100 border-gray-300 text-gray-800'
  },
  {
    id: 'constructivist',
    name: 'Constructivist',
    description: 'Students build knowledge through experience',
    icon: Brain,
    color: 'bg-orange-100 border-orange-300 text-orange-800'
  },
  {
    id: 'problem-based',
    name: 'Problem-Based',
    description: 'Learning through solving real problems',
    icon: Puzzle,
    color: 'bg-red-100 border-red-300 text-red-800'
  },
  {
    id: 'experiential',
    name: 'Experiential',
    description: 'Learning through direct experience and reflection',
    icon: Zap,
    color: 'bg-indigo-100 border-indigo-300 text-indigo-800'
  },
  {
    id: 'competency-based',
    name: 'Competency-Based',
    description: 'Focus on mastering specific skills and competencies',
    icon: GraduationCap,
    color: 'bg-teal-100 border-teal-300 text-teal-800'
  }
];

const PedagogySelector = ({ selected, onChange }) => {
  return (
    <div className="space-y-3">
      {pedagogyOptions.map((option) => {
        const IconComponent = option.icon;
        const isSelected = selected === option.id;
        
        return (
          <div
            key={option.id}
            className={`
              p-3 rounded-lg border-2 cursor-pointer transition-all
              ${isSelected 
                ? `${option.color} border-opacity-100` 
                : 'bg-white border-gray-200 hover:border-gray-300'
              }
            `}
            onClick={() => onChange(option.id)}
          >
            <div className="flex items-start gap-3">
              <IconComponent 
                size={20} 
                className={isSelected ? 'text-current' : 'text-gray-500'} 
              />
              <div className="flex-1">
                <h4 className={`font-medium ${isSelected ? 'text-current' : 'text-gray-900'}`}>
                  {option.name}
                </h4>
                <p className={`text-sm mt-1 ${isSelected ? 'text-current opacity-80' : 'text-gray-600'}`}>
                  {option.description}
                </p>
              </div>
              {isSelected && (
                <div className="w-2 h-2 rounded-full bg-current opacity-80"></div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default PedagogySelector;