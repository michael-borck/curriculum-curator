import React, { useState, useEffect, useCallback } from 'react';
import { Plus, MoreVertical, Calendar, User, Flag, X } from 'lucide-react';
import api from '../../services/api';

interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'complete';
  priority?: 'low' | 'medium' | 'high';
  assignee?: string;
  due_date?: string;
  metadata?: any;
}

interface TaskList {
  id: string;
  unitId: string;
  lrd_id?: string;
  tasks: Task[];
  status: string;
  total_tasks: number;
  completed_tasks: number;
  progressPercentage: number;
  createdAt: string;
  updatedAt: string;
}

interface TaskBoardProps {
  unitId?: string;
  lrdId?: string;
}

const TaskBoard: React.FC<TaskBoardProps> = ({ unitId, lrdId }) => {
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [selectedList, setSelectedList] = useState<TaskList | null>(null);
  const [loading, setLoading] = useState(true);
  const [draggedTask, setDraggedTask] = useState<{
    task: Task;
    index: number;
  } | null>(null);
  const [showTaskDetail, setShowTaskDetail] = useState<Task | null>(null);

  // Columns for Kanban board
  const columns = [
    { id: 'pending', title: 'To Do', color: 'bg-gray-100' },
    { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50' },
    { id: 'complete', title: 'Completed', color: 'bg-green-50' },
  ];

  const fetchTaskLists = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (unitId) params.append('unit_id', unitId);
      if (lrdId) params.append('lrd_id', lrdId);

      const response = await api.get(`/tasks?${params.toString()}`);
      setTaskLists(response.data);

      // Select first list by default
      if (response.data.length > 0 && !selectedList) {
        setSelectedList(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch task lists:', error);
    } finally {
      setLoading(false);
    }
  }, [unitId, lrdId, selectedList]);

  useEffect(() => {
    fetchTaskLists();
  }, [fetchTaskLists]);

  const updateTaskStatus = async (taskIndex: number, newStatus: string) => {
    if (!selectedList) return;

    try {
      const response = await api.patch(
        `/tasks/${selectedList.id}/tasks/${taskIndex}`,
        { status: newStatus }
      );

      // Update local state
      setSelectedList(response.data);
      setTaskLists(lists =>
        lists.map(list => (list.id === response.data.id ? response.data : list))
      );
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleDragStart = (task: Task, index: number) => {
    setDraggedTask({ task, index });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, newStatus: string) => {
    e.preventDefault();
    if (draggedTask) {
      updateTaskStatus(draggedTask.index, newStatus);
      setDraggedTask(null);
    }
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getTasksByStatus = (status: string) => {
    if (!selectedList) return [];
    return selectedList.tasks
      .map((task, index) => ({ ...task, originalIndex: index }))
      .filter(task => task.status === status);
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-96'>
        <div className='text-gray-500'>Loading tasks...</div>
      </div>
    );
  }

  return (
    <div className='h-full flex flex-col'>
      {/* Header */}
      <div className='bg-white border-b px-6 py-4'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center space-x-4'>
            <h2 className='text-2xl font-bold text-gray-900'>
              Task Management
            </h2>
            {selectedList && (
              <div className='flex items-center space-x-2'>
                <div className='text-sm text-gray-500'>
                  {selectedList.completed_tasks} / {selectedList.total_tasks}{' '}
                  tasks
                </div>
                <div className='w-32 bg-gray-200 rounded-full h-2'>
                  <div
                    className='bg-green-600 h-2 rounded-full transition-all'
                    style={{ width: `${selectedList.progressPercentage}%` }}
                  />
                </div>
                <span className='text-sm text-gray-600'>
                  {Math.round(selectedList.progressPercentage)}%
                </span>
              </div>
            )}
          </div>
          <div className='flex items-center space-x-2'>
            <button className='px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700'>
              <Plus className='w-4 h-4 inline mr-1' />
              Add Task
            </button>
          </div>
        </div>

        {/* Task List Selector */}
        {taskLists.length > 1 && (
          <div className='mt-4 flex space-x-2'>
            {taskLists.map(list => (
              <button
                key={list.id}
                onClick={() => setSelectedList(list)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedList?.id === list.id
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                List {list.id.slice(0, 8)}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Kanban Board */}
      <div className='flex-1 overflow-hidden bg-gray-50'>
        <div className='h-full p-6'>
          <div className='grid grid-cols-3 gap-6 h-full'>
            {columns.map(column => (
              <div
                key={column.id}
                className={`${column.color} rounded-lg p-4 flex flex-col`}
                onDragOver={handleDragOver}
                onDrop={e => handleDrop(e, column.id)}
              >
                <div className='flex items-center justify-between mb-4'>
                  <h3 className='font-semibold text-gray-900'>
                    {column.title}
                  </h3>
                  <span className='text-sm text-gray-500'>
                    {getTasksByStatus(column.id).length}
                  </span>
                </div>

                <div className='flex-1 overflow-y-auto space-y-3'>
                  {getTasksByStatus(column.id).map(task => (
                    <div
                      key={task.originalIndex}
                      draggable
                      onDragStart={() =>
                        handleDragStart(task, task.originalIndex)
                      }
                      className='bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-move'
                      onClick={() => setShowTaskDetail(task)}
                    >
                      <div className='flex items-start justify-between mb-2'>
                        <h4 className='font-medium text-gray-900 flex-1'>
                          {task.title}
                        </h4>
                        <button className='text-gray-400 hover:text-gray-600'>
                          <MoreVertical className='w-4 h-4' />
                        </button>
                      </div>

                      {task.description && (
                        <p className='text-sm text-gray-600 mb-3 line-clamp-2'>
                          {task.description}
                        </p>
                      )}

                      <div className='flex items-center justify-between'>
                        <div className='flex items-center space-x-2'>
                          {task.priority && (
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(task.priority)}`}
                            >
                              <Flag className='w-3 h-3 inline mr-1' />
                              {task.priority}
                            </span>
                          )}
                          {task.due_date && (
                            <span className='text-xs text-gray-500'>
                              <Calendar className='w-3 h-3 inline mr-1' />
                              {new Date(task.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        {task.assignee && (
                          <div className='flex items-center text-xs text-gray-500'>
                            <User className='w-3 h-3 mr-1' />
                            {task.assignee}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Task Detail Modal */}
      {showTaskDetail && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto'>
            <div className='flex items-start justify-between mb-4'>
              <h3 className='text-xl font-semibold'>{showTaskDetail.title}</h3>
              <button
                onClick={() => setShowTaskDetail(null)}
                className='text-gray-400 hover:text-gray-600'
              >
                <X className='w-5 h-5' />
              </button>
            </div>

            {showTaskDetail.description && (
              <div className='mb-4'>
                <h4 className='font-medium text-gray-700 mb-2'>Description</h4>
                <p className='text-gray-600'>{showTaskDetail.description}</p>
              </div>
            )}

            <div className='grid grid-cols-2 gap-4 mb-4'>
              <div>
                <h4 className='font-medium text-gray-700 mb-2'>Status</h4>
                <span className='px-3 py-1 bg-gray-100 rounded-full text-sm'>
                  {showTaskDetail.status.replace('_', ' ')}
                </span>
              </div>
              {showTaskDetail.priority && (
                <div>
                  <h4 className='font-medium text-gray-700 mb-2'>Priority</h4>
                  <span
                    className={`px-3 py-1 rounded-full text-sm ${getPriorityColor(showTaskDetail.priority)}`}
                  >
                    {showTaskDetail.priority}
                  </span>
                </div>
              )}
              {showTaskDetail.due_date && (
                <div>
                  <h4 className='font-medium text-gray-700 mb-2'>Due Date</h4>
                  <p className='text-gray-600'>
                    {new Date(showTaskDetail.due_date).toLocaleDateString()}
                  </p>
                </div>
              )}
              {showTaskDetail.assignee && (
                <div>
                  <h4 className='font-medium text-gray-700 mb-2'>Assignee</h4>
                  <p className='text-gray-600'>{showTaskDetail.assignee}</p>
                </div>
              )}
            </div>

            <div className='flex justify-end space-x-2'>
              <button
                onClick={() => setShowTaskDetail(null)}
                className='px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50'
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskBoard;
