import type { InputTask } from "./App";

export default function TaskTable({
    data,
    setData
}: {
    data: InputTask[];
    setData: (updated: InputTask[]) => void;
}) {

    const handleChange = (id: number, field: string, value: any) => {
        setData(
            data.map((task) =>
                task.id === id ? { ...task, [field]: value } : task
            )
        );
    };

    const addTask = () => {
        setData([
            ...data,
            {
                id: data.length + 1,
                length: 1,
                isCache: false,
                useBus: false,
            },
        ]);
    };

    const deleteTask = (id: number) => {
        setData(
            data
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
                                <select
                                    className="border rounded px-2 py-1"
                                    value={task.isCache ? "yes" : "no"}
                                    onChange={(e) =>
                                        handleChange(task.id, "isCache", e.target.value === "yes")
                                    }
                                >
                                    <option value="yes">Yes</option>
                                    <option value="no">No</option>
                                </select>


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
                                <button
                                    onClick={() => deleteTask(task.id)}
                                    className="w-[30px] h-[30px] bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 transition"
                                >
                                    -
                                </button>
                            </td>
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
