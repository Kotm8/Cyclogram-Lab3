import type { InputTask } from "./App";

export default function TaskTable({ data, setData }: { data: InputTask[], setData: React.Dispatch<React.SetStateAction<InputTask[]>> }) {

    const handleChange = (id: number, field: string, value: any) => {
        setData((prev) =>
            prev.map((task) =>
                task.id === id ? { ...task, [field]: value } : task
            )
        );
    };

    const addTask = () => {
        setData((prev) => [
            ...prev,
            {
                id: prev.length + 1,
                length: 1,
                isCache: false,
                useBus: false,
                isDMA: false,
            },
        ]);
    }
    const deleteTask = (id: number) => {
  setData((prev) =>
    prev
      .filter((task) => task.id !== id)          
      .map((task, index) => ({ ...task, id: index + 1 })) 
  );
};

    return (
        <div className="p-4">
            <table className="min-w-full border border-gray-300 rounded-lg overflow-hidden">
                <thead className="bg-gray-100">
                    <tr>
                        <th className="px-4 py-2 border">ID</th>
                        <th className="px-4 py-2 border">Length</th>
                        <th className="px-4 py-2 border">Is Cache</th>
                        <th className="px-4 py-2 border">Use Bus</th>
                        <th className="px-4 py-2 border">Is DMA</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((task) => (
                        <tr key={task.id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border text-center">{task.id}</td>
                            <td className="px-4 py-2 border text-center">
                                <input
                                    type="number"
                                    className="w-16 border rounded px-1 text-center"
                                    value={task.length}
                                    onChange={(e) =>
                                        handleChange(task.id, "length", Number(e.target.value))
                                    }
                                />
                            </td>
                            <td className="px-4 py-2 border text-center">
                                <div className="flex justify-center gap-2">
                                    <label>
                                        <input
                                            type="radio"
                                            name={`isCache-${task.id}`}
                                            checked={task.isCache === true}
                                            onChange={() => handleChange(task.id, "isCache", true)}
                                        />{" "}
                                        Yes
                                    </label>
                                    <label>
                                        <input
                                            type="radio"
                                            name={`isCache-${task.id}`}
                                            checked={task.isCache === false}
                                            onChange={() => handleChange(task.id, "isCache", false)}
                                        />{" "}
                                        No
                                    </label>
                                </div>
                            </td>
                            <td className="px-4 py-2 border text-center">
                                <select
                                    className="border rounded px-2 py-1"
                                    value={task.useBus ? "yes" : "no"}
                                    onChange={(e) =>
                                        handleChange(task.id, "useBus", e.target.value === "yes")
                                    }
                                >
                                    <option value="yes">Yes</option>
                                    <option value="no">No</option>
                                </select>

                            </td>
                            <td className="px-4 py-2 border text-center">
                                <select
                                    className="border rounded px-2 py-1"
                                    value={task.isDMA ? "yes" : "no"}
                                    onChange={(e) =>
                                        handleChange(task.id, "isDMA", e.target.value === "yes")
                                    }
                                >
                                    <option value="yes">Yes</option>
                                    <option value="no">No</option>
                                </select>

                            </td>
                            <button
                                onClick={() => (
                                    deleteTask(task.id))
                                }
                                className="w-[30px] h-[30px] ml-4 mt-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 transition"
                            >
                                -
                            </button>
                        </tr>
                    ))}

                </tbody>
                <tfoot>
                    <tr>
                        <td colSpan={4} className="p-2">
                            <button
                                onClick={addTask}
                                className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 transition"
                            >
                                Add Task
                            </button>
                        </td>
                    </tr>
                </tfoot>
            </table>
        </div>
    );
}
